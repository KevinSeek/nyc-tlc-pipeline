#!/usr/bin/env bash

# Pull-based deploy for nyc-tlc. Run by nyc-tlc-deploy.service as deployer.
# Pull the pipeline image; if it changed, run the smoke flow. Output goes to journald.
set -euo pipefail # stop on any error (-e), on unset variables (-u), and on a failure inside a pipe (pipefail)

cd /opt/nyc-tlc # so Compose finds compose.yml and .env

# Image name(s) Compose resolves for `pipeline`. Only `pipeline` is pulled below
# (`pull` skips depends_on without --include-deps), so only its ID can change.
# Follows IMAGE_TAG in .env, so a rollback pin is respected automatically.
images=$(docker compose config --images pipeline)

# For each image name, print its local ID or 'missing' if it isn't on labby yet (first run).
image_ids() {
    local img
    for img in $images; do
        docker image inspect --format '{{.Id}}' "$img" 2>/dev/null || echo "missing"
    done
}

before=$(image_ids)

# Name the service: a plain `pull` skips `pipeline` because of profiles: [manual].
if ! docker compose pull --quiet pipeline; then
    echo "deploy: PULL FAILED - kept current image"
    exit 1
fi

after=$(image_ids)
if [[ "$before" == "$after" ]]; then
    echo "deploy: no change"
    exit 0
fi

# Unquoted $(echo $before) folds the two lines into one for a single log line.
echo "deploy: image changed: $(echo $before) -> $(echo $after)"

rc=0
docker compose run --rm -T pipeline || rc=$? # -T: no terminal under systemd; `|| rc=$?` keeps -e from exiting before we log

if [[ $rc -eq 0 ]]; then
    echo "deploy: OK - smoke flow exit=0"
else
    echo "deploy: SMOKE FAILED - exit=$rc"
fi
exit "$rc"
