from ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y build-essential curl clang libclang-dev liblz4-dev libssl-dev cmake python3 python3-pip wget unzip
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain 1.75 -y
ENV PATH="/root/.cargo/bin:$PATH"
RUN rustup toolchain install nightly-2023-08-25 -c rustc-dev -c rust-src -c rustfmt -c clippy

RUN mkdir home/aec
WORKDIR home/aec

RUN wget https://github.com/github/codeql-cli-binaries/releases/download/v2.19.3/codeql-linux64.zip
RUN unzip codeql-linux64.zip
RUN rm codeql-linux64.zip
ENV PATH="$PATH:$(realpath codeql)"

RUN mkdir artifact
WORKDIR artifact
ADD plotting/requirements.txt plotting/requirements.txt
RUN python3 -m pip install -r plotting/requirements.txt
ADD . .
RUN cp etc/docker-bench-conf.toml paralegal-bench/bconf/bench-config.toml

RUN cd codeql-experimentation/runner && cargo build --release
RUN cd paralegal-bench && cargo build --release --bin griswold
RUN cd paralegal && cargo build --release -p paralegal-flow



