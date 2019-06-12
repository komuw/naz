#!/usr/bin/env bash
if test "$BASH" = "" || "$BASH" -uc "a=();true \"\${a[@]}\"" 2>/dev/null; then
    # Bash 4.4, Zsh
    set -euo pipefail
else
    # Bash 4.3 and older chokes on empty arrays with set -u.
    set -eo pipefail
fi
shopt -s nullglob globstar

export DEBIAN_FRONTEND=noninteractive && \
apt -y update && \
apt -y install python && \
apt -y install python-pip python3-pip nano wget unzip curl screen

# NB: do not install docker from snap; it is broken
apt -y remove docker docker-engine docker.io containerd runc docker-ce docker-ce-cli && \
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
apt-key fingerprint 0EBFCD88 && \
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
apt -y update; apt -y autoremove && \
apt -y install docker-ce && \
usermod -aG docker $(whoami) && \
pip install -U docker-compose

wget https://github.com/komuw/naz/archive/master.zip && \
unzip master.zip && \
mv naz-master/ naz && \
cd naz/benchmarks


# A. SMSC SERVER
# 1. start screen
pip3 install -e ..[benchmarks]
export REDIS_PASSWORD=hey_NSA && python3 smpp_n_queue_servers.py &>/dev/null &
disown

# A. NAZ-CLI
# 1. start screen
# 2. edit `compose.env`(if neccesary)
docker-compose up --build &>/dev/null &
disown
