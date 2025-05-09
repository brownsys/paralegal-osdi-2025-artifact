renamings_for_display = {
    # Columns in results.csv
    'id': 'Id', 
    'experiment': 'Experiment', 
    'mode': 'Mode', 
    'application': 'Application', 
    'controller': 'Controller',
    'ablation_feature': 'Ablation Feature', 
    'commit': 'Commit', 
    'bug': 'Lemmy Bug', 
    'package': 'Target Package', 
    'run': 'Run Name', 
    'policy': 'Policy',
    'expectation': 'Expected Outcome', 
    'adaptive_depth': 'Adaptive Approximation', 
    'pdg_caching': 'PDG Caching', 
    'result': 'Outcome',
    'pdg_timed_out': 'Timeout Reached', 
    'analyzer_time': 'Total Analyzer Time', 
    'last_self_time': 'Last Flow Time', 
    'dep_time': 'Dep. Comp. CPU Time',
    'tycheck_time': 'Typechecking Time', 
    'dump_time': 'Dep. Dump CPU Time', 
    'rustc_time': 'Rustc time', 
    'policy_time': 'Policy Runtime',
    'serialization_time': 'Serialization Time', 
    'deserialization_time': 'Deserialization Time', 
    'precomputation_time': 'Policy Context Precomputation Time',
    'traversal_time': 'Policy Check Time', 
    'num_controllers': '# Controllers', 
    'num_markers': '# Attached Markers', 
    'pdg_functions': 'Functions in PDG',
    'pdg_locs': '# LoC in PDG', 
    'seen_functions': 'Functions Analyzed', 
    'seen_locs': '# LoC Analyzed', 
    'changed_lines': '# LoC Changed', 
    'file_size': 'File Size',
    'peak_mem_usage_pdg': 'Peak Mem Usage PDG', 
    'mean_mem_usage_pdg': 'Mean Mem Usage PDG', 
    'peak_cpu_usage_pdg': 'Peak CPU Usage PDG',
    'mean_cpu_usage_pdg': 'Mean CPU Usage PDG', 
    'peak_mem_usage_policy': 'Peak Mem Usage Policy', 
    'mean_mem_usage_policy': 'Mean Mem Usage Policy',
    'peak_cpu_usage_policy': 'Peak CPU Usage Policy', 
    'mean_cpu_usage_policy': 'Mean CPU Usage Policy',

    # calculated values
    'io_time': 'PDG I/O',
    'pdg_time': 'PDG Construction',

    # application names
    'lemmy': 'Lemmy',
    'lemmy-new': 'Lemmy',
    'atomic-data': 'Atomic Data',
    'hyperswitch': 'Hyperswitch',
    'contile': 'Contile',
    'websubmit': 'Websubmit',
    'freedit': 'Freedit',
    'mcaptcha': 'mCaptcha',
    'plume': 'Plume',
}

def rename(n):
    return renamings_for_display.get(n, n)

def _expand_dict_w_rename(d):
    return {
        k1: v
        for k, v in d.items()
        for k1 in [k, rename(k)]
    }

SYSTEM_COLORS = _expand_dict_w_rename({
  'flow_time': 'C0',
  'policy_time': 'C6',
  'rustc_time': 'C11',
  'serialization_time': 'C12',
  "atomic-data": "C1",
  "plume": "C2",
  "freedit": "C3",
  "websubmit": "C4",
  "hyperswitch": "C5",
  "contile": "C7",
  "lemmy": "C8",
  "baseline": "C10",
  "opt": "C9",
  "mcaptcha": "C9",
})

SYSTEM_MARKERS = _expand_dict_w_rename({
    "atomic-data": "^",
    "plume": "v",
    "freedit": "+",
    "websubmit": "o",
    "hyperswitch": "s",
    "contile": "d",
    "lemmy": "x",
    "mcaptcha": "D",
})