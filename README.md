# Artifact for the submission of "Paralegal" to OSDI 2025

Welcome to the software artifact for the 2025 submission of the static Rust
privacy and security analyzer "Paralegal". This repository ties together the
analyzer, benchmark suite and plotting utilities for reproducing the
graphs shown in the paper.

**This repository is intended for artifact evaluators. If you are interested in
using the software (or benchmarker), you should instead visit the standalone
repos for [the "Paralegal" analyzer](https://github.com/brownsys/paralegal) or
[the benchmarker](https://github.com/brownsys/paralegal-bench), which
have the latest updates.**

If you are intending to use this artifact from its repository, go to the [Setup
and Installation](#setup-and-installation) section **before cloning the repo**.

If you are receiving this artifact as a docker container you'll likely want to
skip directly to [Step by step for reproducing
results](#step-by-step-for-reproducing-results).

## Platform compatibility

The **analyzer** has been tested on Ubuntu and OSX, but should in theory run on any
Linux and possibly Windows too, though no guarantees are made.

The **benchmarker** relies on UNIX features (process groups) and can only run on a
platform that supports it e.g. Linux and OSX.

## Setup and installation

**If this artifact was provided to you as a docker container, you may skip this section.**

This artifact leverages git submodules so you must clone with `--recursive` or
run `git submodule init && git submodule update` after cloning.

```bash
$ git clone git@github.com:brownsys/paralegal-osdi-2025-artifact --recursive
```

You should have [`rustup`](https://rustup.rs/) installed on your system, to
handle the Rust toolchain management. This is necessary because the analyzer
builds against a specific Rust nightly version (see
`paralegal/rust-toolchain.toml`). For Unix you can run 

```bash
$ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain none
```

Rustup will install the requisite toolchains automatically. You can download the
one necessary for the analyzer and verify that the rustup installation was
successful by running

```bash
$ (cd paralegal && rustc --version)
...
rustc 1.74.0-nightly (58eefc33a 2023-08-24)
```

You will also require python 3 to plot the graphs. Please follow the installation
instruction for your platform.

**This next set of instructions is only if you are operating on Linux.** 

Retrieve the system root for the Rust toolchain, e.g. with my example output

```bash
(cd paralegal && rustc --print sysroot)
/home/justus/.rustup/toolchains/nightly-2023-08-25-x86_64-unknown-linux-gnu
```

You must edit any benchmark configuration (e.g.
`paralegal-bench/bconf/bench-config.toml`) you run. Specifically it will have an
entry like 

```toml
[app-config.hyperswitch.env]
LD_LIBRARY_PATH = "TOOLCHAIN/lib"
```

Replace the `TOOLCHAIN` part with the sysroot path you retrieved.

```toml
[app-config.hyperswitch.env]
LD_LIBRARY_PATH = "/home/justus/.rustup/toolchains/nightly-2023-08-25-x86_64-unknown-linux-gnu/lib"
```

For the curious: this is a workaround to deal with cases where a build script
calls `rustc` to get metadata information. This actually ends up calling our
analyzer again (which wraps around `rustc`), which dynamically links against
`libLLVM`, but for some reason in this nested call the linker cannot find this
library, so we provide the path here.

## Step-by-step for reproducing results

You can run the entire benchmark with

```bash
$ (cd paralegal-bench && cargo run --bin griswold --release -- bconf/bench-config.toml)
```

Some notes on this configuration (`bconf/bench-config.toml`):

- In the paper we run these experiments with 5 repetitions to ensure stable
  results. This option is commented out in the configuration provided to you, as
  the numbers tend to be similar even for just one run and this makes the
  overall runtime almost 5 times lower. If you so desire, you may comment the
  option back in at the top of the file.
- The timeout set in the configuration is 5 minutes, whereas in the paper we say
  the PDG construction for Lemmy times out in 10min. We have tested it with
  10min, the limit of 5 here is for your convenience. You may test different
  ones if you so desire.

## Organization

**Make sure you've fetched the submodules by cloning with `--recursive` or
running `git submodule init && git submodule update`**

This artifact is organized as follows:

- The `paralegal` directory contains the source code for the analyzer. The most
  important subdirectories are

  - `crates/paralegal-flow` is the PDG constructor. It wraps around `cargo` and
    `rustc`, functioning as a compiler plugin. It can be installed via `cargo
    install --locked --path crates/paralegal-flow` and run via `cargo
    paralegal-flow` in the directory of a target rust project to analyze. It
    also accepts a `--help` flag to show command line configuration options.
  - `crates/paralegal-policy` contains the low-level Rust API for policy
    enforcement, which is used by the compiler (`paralegal-compiler`).
  - `crates/paralegal` is the annotation library that a target rust project
    should link against to add inline annotations, e.g. `#[paralegal::analyze]`
    or `#[paralegal::marker(...)]`.

  For more documentation on the analyzer see the [online
  documentation](https://brownsys.github.io/paralegal).

- The `paralegal-bench` directory contains the benchmark coordinator and source
  code for our use cases.

  - `bconf` contains configuration files for various benchmark runs. The most
    important one being `bench-config.toml`, which is the one used to produce
    all results we present in the paper.
  - `griswold` is the benchmark driver/coordinator. You can run it via `cargo
    run --bin griswold`. It takes as input a run configuration (for example
    `bconf/bench-config.toml`). It writes outputs to the `results` directory.
    See the `--help` option of the [Benchmarker output
    Format](#benchmarker-output-format) section for more details on the
    structure of results.
  - `case-studies` contains a copy of the source code for our case studies.
    These corresponds to the commits listed in [Case study
    versions](#case-study-versions) with some small changes applied as explained
    in the paper appendix.
  - `paralegal-compiler` contains the source code for the compiler of the
    high-level policy language. Can be run via `cargo run -p
    paralegal-compiler --release`.

    - The policies used in the paper and corresponding to our case studies are
      in the `policies` subdirectory.

- The `plotting` directory contains python scripts to plot the graphs. Install
  the dependencies with `python3 -m pip install -r plotting/requirements.txt`.

## Benchmarker output format

This section explains the output structure create by the `griswold` benchmark coordinator.

Results are written to the `--result-path` argument (default to "results"). Each
time you call `griswold` it creates a new set of directories. They all have
the format `<timestamp>-<purpose>` with the following purposes:

- `logs`: stdout and stderr from the PDG generation (called `compile`) and
  combined output from the policy 
  
- `pp`: The source code that was involved in the analysis. The lines of code
  actually visited. This is used in the roll-forward experiment
- `run`: Everything considered result data which are the following files:

  - `results.csv`: incrementally written statistics and results for each run.
  - `controllers.csv`: incrementally written statistics about individual
    controllers. 
    
    Multiple such statistics are written for a single run. The `run_id` field
    tells you which run each row belongs to. 
  - `sys.toml`: information about the system that this experiment was run on.
  - `bench-config.toml`: a copy of the configuration that was input to this run

## Case study versions

| Application | Source Repo | Commit |
| --- | --- | --- |
| Atomic Data | https://github.com/atomicdata-dev/atomic-server | `46a503adbfc52678c97e52f6e8cfaf541aa6492d` |
| Contile | https://github.com/mozilla-services/contile | `2bdf4072925d199c1b75d1f76f656c34325e5e8a` |
| Freedit | https://github.com/freedit-org/freedit | `b25e3781a8f46506046bb92f9bfc1ce85a9c9b6d` |
| Hyperswitch | https://github.com/juspay/hyperswitch | `6428d07f983026245159de4147b62bc0fc018165` |
| Lemmy | https://github.com/LemmyNet/lemmy | `b78826c2c80567192b4e2ce5f8714a094299be04` |
| mCaptcha | https://github.com/mCaptcha/mCaptcha/ | `9922c233220751e9611b42414ecd82fcde757480` |
| Plume | https://github.com/Plume-org/Plume | `613ccbcd945618cce624725aee3e2997cbf6de38` |
| Websubmit | https://github.com/JustusAdam/beavered-websubmit | `4b4713845494b14e92b01c05ec32e7d429eb524f` |