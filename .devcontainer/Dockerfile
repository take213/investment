FROM python:3.11

RUN python -m pip install --no-cache-dir uv==0.13.8

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
    bash-completion && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*