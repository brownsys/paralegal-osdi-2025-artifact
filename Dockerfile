from ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y build-essential curl clang libclang-dev liblz4-dev libssl-dev cmake python3 python3-pip wget unzip pkg-config git
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain 1.75 -y
ENV PATH="/root/.cargo/bin:$PATH"
RUN rustup toolchain install nightly-2023-08-25 -c rustc-dev -c rust-src -c rustfmt -c clippy

RUN mkdir home/aec
WORKDIR home/aec

RUN wget https://github.com/github/codeql-cli-binaries/releases/download/v2.19.3/codeql-linux64.zip\ 
    && tar -xf codeql-bundle-linux64.tar.gz \
    && rm codeql-bundle-linux64.tar.gz
ENV PATH="$PATH:/home/aec/codeql"

RUN git clone https://github.com/atomicdata-dev/atomic-server 

RUN mkdir artifact
WORKDIR artifact
ADD plotting/requirements.txt plotting/requirements.txt
RUN python3 -m pip install -r plotting/requirements.txt
ADD . .
RUN cp etc/docker-bench-conf.toml paralegal-bench/bconf/bench-config.toml

# Download the dependencies. There's no native way to do *just* that so we use check 
# instead and throw away any potential build artifacts
RUN cd codeql-experimentation/runner && cargo check --locked && cargo clean
RUN cd paralegal-bench && cargo check --locked && cargo clean
RUN cd paralegal && cargo check --locked && cargo clean
RUN for i in $(ls paralegal-bench/case-studies/); do (cd "paralegal-bench/case-studies/$i" && cargo +nightly-2023-08-25 check && cargo +nightly-2023-08-25 clean); done



