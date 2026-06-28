#!/bin/sh

WORKDIR="$(realpath "$(dirname "$0")")"

# shellcheck disable=SC2155
export USER="$(id -un)"
export COMMAND="cd ${WORKDIR} && ${HOME}/.local/bin/uv run ${WORKDIR}/main.py"

sudo apt install gettext # envsubst
envsubst <techdigest.cron | sudo tee /etc/cron.d/techdigest

# install browsers
uv sync
.venv/bin/playwright install
sudo .venv/bin/playwright install-deps
