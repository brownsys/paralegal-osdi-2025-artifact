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
        help="Path to the input CSV file containing the results.",
    )
    parser.add_argument(
        "-e",
        "--experiment",
        type=str,
        default=None,
        action='append',
        help="Generate plots for this experiment. Defaults to all.",
        nargs="*",
        choices=[
            p.name() for p in plots
        ]
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


    results_dir = args.input
    all_results = pd.read_csv(results_dir + "/results.csv")
    controller_stats = pd.read_csv(results_dir + "/controllers.csv")
    all_results[timings] /= 1_000_000
    results = all_results[all_results['result'].notna()]
    if not args.experiment:
        to_run = plots
    else:
        to_run = [
            p for p in plots
            if p.name() in args.experiment
        ]
    
    for plot in to_run:
        print(f"Running {plot.name()}...")
        plot(f"{plot.name()}{plot.output_ext}")

@plot(output_ext=".png")
def ide_ci_plot(outfile):
    e = results[results['experiment'].isin(['ide', 'ci'])].copy()
    e['io_time'] = e['serialization_time'] + e['deserialization_time']
    e['pdg_time'] = e['last_self_time'] - e['rustc_time'] - e['serialization_time']
    e['policy_time'] -= e['deserialization_time']
    metrics = ['rustc_time', 'pdg_time', 'policy_time', 'io_time']
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
    plot1.set_title("CI Setup")
    plot1.set_ylabel("Runtime in s")
    plot1.set_xlabel("Application")
    
    plot2 = e[e['experiment'] == 'ide']\
        .groupby('application')\
        [metrics].mean()\
        .rename(index= lambda x: x.removesuffix("-ide"))\
        .rename(index=utils.rename, columns=utils.rename)\
        .plot.bar(ax=ax2, stacked=True)
    plot2.set_title("IDE Setup")
    
    plot2.set_xlabel("Application")

    plt.savefig(outfile)

@plot(output_ext=".png")
def per_controller_plot(outfile):
    e = results[results['experiment'].isin(['per-controller-time'])].copy()
    e['ctrl_time'] = e['last_self_time'] - e['rustc_time'] + e['policy_time']
    metrics = ['ctrl_time', 'pdg_locs']
    # This combines the repeated runs
    e = e.groupby(['application', 'controller', 'package'], dropna=False)[metrics].mean()\
        .rename(index=lambda x: x.removesuffix("-ide") if isinstance(x, str) else x)
    e = e.reset_index()
    fig, ax = plt.subplots()
    for a in e['application'].unique():
        e[e['application'] == a].plot.scatter(ax=ax, x='pdg_locs', marker=utils.SYSTEM_MARKERS[a], y='ctrl_time', color=utils.SYSTEM_COLORS[a], label=utils.rename(a))
    ax.set_title("PDG Construction and Policy Time per Controller")
    ax.set_xlabel("LoC in PDG")
    ax.set_ylabel("Time in s")

    plt.savefig(outfile)

@plot(output_ext=".png")
def k_depth_plot(outfile):
    e = all_results[all_results['experiment'].isin(['k-depth', 'ci'])].copy()
    e['total_time'] = e['last_self_time'] + e['policy_time']
    metrics = ['total_time', 'k_depth']
    # This combines the repeated runs
    e = e.groupby(['experiment', 'application', 'package'], dropna=False)[metrics].mean()
    # This recombines the lemmy packages
    e = e.groupby(['experiment', 'application'])[metrics].aggregate({
        'total_time': 'sum',
        'k_depth': 'max',
    })

    k_depth_setting = {
        'lemmy': 24,
        'plume': 19,
    }

    e_k = e.loc['k-depth']
    series = e.loc['ci'] / e_k
    plot = series[['total_time']].rename(index=utils.rename).plot.bar()
    plot.axhline(1.0, ls='--', color='k', label="no adaptive inlining")
    
    for (i, (app, row)) in enumerate(series.iterrows()):
        val = row['total_time']
        if np.isinf(val) or pd.isna(val):
            val = 0
            plot.plot(i, 0.12, color="black", marker='x', markersize=3)
            plot.text(i, 0.15, "timeout", ha='center', va='bottom', rotation='vertical')
        if app in e_k.index:
            k = e_k.loc[app]['k_depth']
        else:
            # Account for config where timeouts are commented out
            k = k_depth_setting[app]
        plot.text(i, val, "k = " + str(int(k)), ha='center', va='bottom')
    plot.set_title("Relative Runtime of k-depth vs Adaptive Approximation")
    plot.set_ylabel("Runtime Relative to k-depth")
    plot.set_xlabel("Application")

    plt.savefig(outfile)

@plot(output_ext=".png")
def old_adaptive_plot(outfile):
    e = all_results[all_results['experiment'].isin(['adaptive-depth', 'ide'])].copy()
    e['total_time'] = e['last_self_time'] + e['policy_time']
    metrics = ['total_time', 'k_depth']
    # This combines the repeated runs
    e = e.groupby(['experiment', 'application', 'package'], dropna=False)[metrics].mean()
    # This recombines the lemmy packages
    e = e.groupby(['experiment', 'application'])[metrics].aggregate({
        'total_time': 'sum',
        'k_depth': 'max',
    })

    series = e.loc['ide'] / e.loc['adaptive-depth']
    plot = series[['total_time']]\
        .rename(index= lambda x: x.removesuffix("-ide"))\
        .rename(index=utils.rename, columns=utils.rename)\
        .plot.bar(legend=False)
    plot.axhline(1.0, ls='--', color='k', label="no adaptive inlining")
    plot.set_title("Adaptive Inlining Runtime Relative to Inlining All")
    plot.set_ylabel("Relative PDG Construction and Policy Runtime")
    plot.set_xlabel("Application")

    plt.savefig(outfile)

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
    e = all_results[all_results['experiment'].isin(['atomic-roll-forward'])].copy()
    e_compiling = e[e['result'].notna()]
    c = e_compiling['changed_lines']
    c = c[c != 0]
    with open(outfile, 'w') as f:
        print("Statistics about checked commits", file=f)
        print(file=f)
        frame = pd.Series({
            'Commits Checked': e.shape[0],
            'Commits Compiling': e_compiling.shape[0],
            'Avg Lines Touched': e_compiling['seen_locs'].mean(),
        })
        frame.to_string(buf=f)
        print(file=f)
        print("Statistics for commits that change code touched by Paralegal", file=f)
        print(file=f)
        c.aggregate(['count', 'min', 'max', 'mean']).rename({
            'count': 'Commits changing lines',
            'min': 'Smallest non-zero change',
            'max': 'Largest #LoC changed in single commit',
            'mean': 'Mean #Loc changed per non-zero change commit',
        }).to_string(buf=f)

plots = [
    ide_ci_plot,
    per_controller_plot,
    k_depth_plot,
    old_adaptive_plot,
    dependency_times,
    atomic_data_locs,
]

main()