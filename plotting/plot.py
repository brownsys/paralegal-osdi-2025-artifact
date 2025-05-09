#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.append(".")
import utils
import argparse
import os
import functools
from datetime import datetime

timings = ['dep_time', 'serialization_time', 'rustc_time', 'dump_time', 'policy_time', 'last_self_time', 'analyzer_time', 'deserialization_time', 'traversal_time']


class PlotDescriptor:
    def __init__(self, output_ext, func):
        self.func = func
        self.output_ext = output_ext

    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)

    def name(self):
        return self.func.__name__

def plot(output_ext=None):
    return functools.partial(PlotDescriptor, output_ext)

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    global args, results_dir, all_results, results, controller_stats
    parser = argparse.ArgumentParser(description="Plotting script for the results of the experiments.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to the input CSV file containing the results. Defaults to the one with the latest timestamp in the paralegal-bench/results directory.",
    )
    parser.add_argument(
        "-e",
        "--experiment",
        type=str,
        default=None,
        action='append',
        help="Generate plots for this experiment. Defaults to all.",
        choices=[
            p.name() for p in plots
        ]
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output directory for the plots (must exist). Defaults to directory this script is stored in.",
    )
    args = parser.parse_args()

    if args.input is None:
        results_dir = "../paralegal-bench/results"
        subdirs = [
            d for d in os.listdir(results_dir)
            if os.path.isdir(os.path.join(results_dir, d)) and "-run" in d
        ]

        if not subdirs:
            raise FileNotFoundError("No subdirectories with the expected format found in the results directory.")

        latest_subdir = max(subdirs, key=lambda d: datetime.strptime(d.removesuffix("-run"), "%Y-%m-%dT%H-%M-%S"))
        args.input = os.path.join(results_dir, latest_subdir)

    output_dir = args.output if args.output is not None else os.path.dirname(os.path.abspath(__file__))
    results_dir = args.input
    all_results = pd.read_csv(results_dir + "/results.csv")
    controller_stats = pd.read_csv(results_dir + "/controllers.csv")
    all_results[timings] /= 1_000_000
    results = all_results[all_results['result'].notna()]
    if not args.experiment:
        to_run = plots
    else:
        print(args.experiment)
        options = { p.name(): p for p in plots }
        to_run = [
            options[p] for p in args.experiment
        ]
    
    for plot in to_run:
        print(f"Running {plot.name()}...")
        plot(os.path.join(output_dir, f"{plot.name()}{plot.output_ext}"))

@plot(output_ext=".png")
def ide_ci_plot(outfile):
    e = results[results['experiment'].isin(['ws', 'ci'])].copy()
    e['io_time'] = e['serialization_time'] + e['deserialization_time']
    e['pdg_time'] = e['last_self_time'] - e['rustc_time'] - e['serialization_time']
    e['policy_time'] -= e['deserialization_time']
    metrics = ['rustc_time', 'pdg_time', 'policy_time', 'serialization_time', 'deserialization_time']
    # This combines the repeated runs
    e = e.groupby(['experiment', 'application', 'package'], dropna=False)[metrics].mean()
    # This recombines the lemmy packages
    e = e.groupby(['experiment', 'application'])[metrics].sum()
    e = e.reset_index()
    fig, (ax1, ax2) = plt.subplots(1, 2)
    plot1 = e[e['experiment'] == 'ci']\
        .groupby('application')\
        [metrics].mean()\
        .rename(index=utils.rename, columns=utils.rename)\
        .plot.bar(ax=ax1, stacked=True)
    plot1.set_title("All Crates")
    plot1.set_ylabel("Runtime in s")
    plot1.set_xlabel("Application")
    
    plot2 = e[e['experiment'] == 'ws']\
        .groupby('application')\
        [metrics].mean()\
        .rename(index= lambda x: x.removesuffix("-ws"))\
        .rename(index=utils.rename, columns=utils.rename)\
        .plot.bar(ax=ax2, stacked=True)
    plot2.set_title("Workspace Crates Only")
    
    plot2.set_xlabel("Application")

    plt.savefig(outfile, bbox_inches='tight')

@plot(output_ext=".png")
def per_controller_plot(outfile):
    e = results[results['experiment'].isin(['per-controller-time'])].copy()
    e['ctrl_time'] = e['last_self_time'] - e['rustc_time'] + e['policy_time']
    metrics = ['ctrl_time', 'pdg_locs']
    # This combines the repeated runs
    e = e.groupby(['application', 'controller', 'package'], dropna=False)[metrics].mean()\
        .rename(index=lambda x: x.removesuffix("-ws") if isinstance(x, str) else x)
    e = e.reset_index()
    fig, ax = plt.subplots()
    apps = e['application'].unique()
    last = apps[apps != 'Lemmy']
    for a in ['Lemmy'] + list(last):
        e[e['application'] == a].plot.scatter(ax=ax, x='pdg_locs', marker=utils.SYSTEM_MARKERS[a], y='ctrl_time', color=utils.SYSTEM_COLORS[a], label=utils.rename(a))
    ax.set_title("PDG Construction and Policy Time per Controller")
    ax.set_xlabel("LoC in PDG")
    ax.set_ylabel("Time in s")

    plt.savefig(outfile, bbox_inches='tight')

@plot(output_ext=".png")
def k_depth_plot(outfile):
    e0 = all_results[all_results['experiment'].isin(['k-depth', 'ci'])].copy()
    e0['application'] = e0['application'].apply(utils.rename)
    e0['total_time'] = e0['last_self_time'] + e0['policy_time']
    metrics = ['total_time', 'k_depth']
    # This combines the repeated runs
    e = e0.groupby(['experiment', 'application', 'package'], dropna=False)[metrics].mean()
    # This recombines the lemmy packages
    e = e.groupby(['experiment', 'application'])[metrics].aggregate({
        'total_time': 'sum',
        'k_depth': 'max',
    })

    k_depth_setting = {
        'Lemmy': 24,
    }

    frame = pd.DataFrame({
        'Adaptive': e.loc['ci']['total_time'],
        'Fixed k': e.loc['k-depth']['total_time'],
    })#.rename(index=utils.rename)

    plot = frame.plot.bar()

    max_y = max(frame.max())
    
    e_k = e.loc['k-depth']
    for (i, (app, row)) in enumerate(frame.iterrows()):
        k_val = row['Fixed k']
        k_is_nn = np.isinf(k_val) or pd.isna(k_val)
        if k_is_nn:
            k_val = 0
        if k_is_nn or e0[(e0['application'] == app) & (e0['experiment'] == 'k-depth')]['total_time'].hasnans:
            offset = 0.12
            plot.plot(i + offset, k_val + max_y * 0.07, color="black", marker='x', markersize=3)
            plot.text(i + offset, k_val + max_y * 0.1, "timeout", ha='center', va='bottom', rotation='vertical')
        if app in e_k.index:
            k = e_k.loc[app]['k_depth']
        else:
            # Account for config where timeouts are commented out
            k = k_depth_setting[app]
        val = max(k_val, row['Adaptive'])
        plot.text(i, val, "k = " + str(int(k)), ha='center', va='bottom')

    plt.savefig(outfile, bbox_inches='tight')

@plot(output_ext=".png")
def old_adaptive_plot(outfile):
    e = all_results[all_results['experiment'].isin(['adaptive-depth', 'ws'])].copy()
    e['total_time'] = e['last_self_time'] + e['policy_time']
    metrics = ['total_time', 'k_depth']
    # This combines the repeated runs
    e = e.groupby(['experiment', 'application', 'package'], dropna=False)[metrics].mean()
    # This recombines the lemmy packages
    e = e.groupby(['experiment', 'application'])[metrics].aggregate({
        'total_time': 'sum',
        'k_depth': 'max',
    })

    series = e.loc['ws'] / e.loc['adaptive-depth']
    plot = series[['total_time']]\
        .rename(index= lambda x: x.removesuffix("-ws"))\
        .rename(index=utils.rename, columns=utils.rename)\
        .plot.bar(legend=False)
    plot.axhline(1.0, ls='--', color='k', label="no adaptive inlining")
    plot.set_title("Adaptive Inlining Runtime Relative to Inlining All")
    plot.set_ylabel("Relative PDG Construction and Policy Runtime")
    plot.set_xlabel("Application")

    plt.savefig(outfile, bbox_inches='tight')

@plot(output_ext=".txt")
def dependency_times(outfile):
    e = results[results['experiment'].isin(['total-runtime'])].copy()
    e['Wall Clock Dependency Time'] = e['analyzer_time'] - e['last_self_time']
    e['Dump Time % Share'] =  e['dump_time'] / e['dep_time'] * 100
    metrics = ['Wall Clock Dependency Time', 'dep_time', 'dump_time', 'Dump Time % Share']
    # This combines the repeated runs
    e = e.groupby(['application', 'package'], dropna=False)[metrics].mean()
    # This recombines the lemmy packages
    e = e.groupby(['application'])[metrics].sum()

    with open(outfile, 'w') as f:
        e[metrics].rename(columns=utils.rename, index=utils.rename).to_string(buf=f)

@plot(output_ext=".txt")
def atomic_data_locs(outfile):
    e = all_results[all_results['experiment'].isin(['atomic-roll-forward', 'atomic-roll-forward-ws'])].copy()
    ws = e[e['application'] == 'roll-forward-atomic-ws']
    cc = e[e['application'] == 'roll-forward-atomic']
    assert ws.shape == cc.shape
    ws_compiling = ws[ws['result'].notna()]
    wsc = ws_compiling['changed_lines']
    wsc = wsc[wsc != 0]
    cc_compiling = cc[cc['result'].notna()]
    ccc = cc_compiling['changed_lines']
    ccc = ccc[ccc != 0]
    with open(outfile, 'w') as outfile:
        print("Statistics about checked commits\n", file=outfile)
        frame = pd.Series({
            'Commits Checked': cc.shape[0],
            'Commits Compiling': ws_compiling.shape[0],
            'Avg Lines Touched Across All Crates': cc_compiling['seen_locs'].mean(),
            'Avg Lines Touched in the Workspace': ws_compiling['seen_locs'].mean(),
        })
        frame.to_string(buf=outfile)
        print(file=outfile)
        print("Statistics for commits that change code touched by Paralegal\n", file=outfile)
        frame2 = pd.DataFrame({
            'LoC Including Deps': ccc,
            'LoC Workspace': wsc,
        })
        frame2.aggregate(['count', 'min', 'max', 'mean']).rename({
            'count': 'Commits changing lines',
            'min': 'Smallest non-zero change',
            'max': 'Largest #LoC changed in single commit',
            'mean': 'Mean #Loc changed per non-zero change commit',
        }).to_string(buf=outfile)


plots = [
    ide_ci_plot,
    per_controller_plot,
    k_depth_plot,
    old_adaptive_plot,
    dependency_times,
    atomic_data_locs,
]

main()
