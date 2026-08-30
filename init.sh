#!/bin/sh

WORKDIR="$(realpath "$(dirname "$0")")"

# shellcheck disable=SC2155
export USER="$(id -un)"
export COMMAND="cd ${WORKDIR} && ${HOME}/.local/bin/uv run ${WORKDIR}/main.py"

cat <<'__EOF__' | envsubst |
#/etc/cron.d/techdigest

# every 1h
# min hour day month weekday user command
0 * * * * ${USER} ${COMMAND}
__EOF__
sudo tee /etc/cron.d/techdigest

# install browsers
uv sync
.venv/bin/playwright install
sudo .venv/bin/playwright install-deps
