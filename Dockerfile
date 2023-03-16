# syntax=docker/dockerfile:1.3-labs
ARG PYTHON_VERSION=3.11.2
FROM "python:${PYTHON_VERSION}"

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/user/.local/bin:$PATH

RUN <<EOF
    set -eu

    apt-get update
    apt-get install -y \
        gosu
    apt-get clean
    rm -rf /var/lib/apt/lists/*

    groupadd -o -g 1000 user
    useradd -m -o -u 1000 -g user user
EOF

ADD ./requirements.txt /tmp/requirements.txt
RUN <<EOF
    set -eu

    gosu user pip3 install --no-cache-dir -r /tmp/requirements.txt
EOF

ADD ./aoirint_psdlayer2dirpy /opt/aoirint_psdlayer2dirpy

ENTRYPOINT [ "gosu", "user", "python3", "/opt/aoirint_psdlayer2dirpy/main.py" ]
