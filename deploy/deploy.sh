#!/usr/bin/env bash

# Pull-based deploy for nyc-tlc. Run by nyc-tlc-deploy.service as deployer.
# Pull the pipeline image; if it changed, run the smoke flow. Output goes to journald.
# *No pipes yet; guards future `|` edits
set -euo pipefail # stop on any error (-e), on unset variables (-u), and on a failure inside a pipe (pipefail)

cd /opt/nyc-tlc # so Compose finds compose.yml and .env

# Image name(s) Compose resolves for `pipeline` (prefect included via depends_on).
# Only `pipeline` is pulled below (`pull` skips depends_on without --include-deps), so only its ID can change.
# * Follows IMAGE_TAG in .env, so a rollback pin is respected automatically.
images=$(docker compose config --images pipeline)

# For each image name, print its local ID or `missing` if it isn't on homelab yet (first run).
image_ids() {
    local img

    for img in $images; do
        docker image inspect --format '{{.Id}}' "$img" 2>/dev/null || echo "missing"
    done
}

# Snapshot local image IDs before the pull (both images; `missing` on first run)
before=$(image_ids)

# Name the service: a plain docker compose `pull` skips `pipeline` because of profiles: [manual].
if ! docker compose pull --quiet pipeline; then
    echo "deploy: PULL FAILED - kept current image"
    exit 1
fi

# Same function as `before`
after=$(image_ids)

# Quoted both sides = literal string compare (unquoted right side would be a glob pattern).
# * No change is the normal outcome (most runs) -> exit 0 so systemd doesn't mark the run failed.
if [[ "$before" == "$after" ]]; then
    echo "deploy: no change"
    exit 0
fi

# Unquoted $( echo $before) folds the 2 lines into one for a single log line.
echo "deploy: image changed: $(echo $before) -> $(echo $after)"

# Assume success; `|| rc=$?` below only runs on failure, so without this
# a successful run leaves `rc` unset and `-u` would exit the script on $rc.
rc=0

# One-off smoke run. `--rm`: remove the container after; `-T`: no TTY (none under systemd).
# `|| rc=$?` records the exit code without letting `-e` exit before we log it.
docker compose run --rm -T pipeline || rc=$?

# `-eq` = numeric compare (exit code are numbers).
if [[ $rc -eq 0 ]]; then
    echo "deploy: OK - smoke flow exit=0"
else
    echo "deploy: SMOKE FAILED - exit=$rc"
fi

# systemd sees only the exit code -> pass on the smoke flow's own code (0 = success, non-zero = failed unit).
exit "$rc"
