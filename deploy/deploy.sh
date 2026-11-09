#!/usr/bin/env bash

# Pull-based deploy for nyc-tlc. Run by nyc-tlc-deploy.service as deployer
# Pull the pipeline image; if it changed, run the smoke flow. Output goes to journald.
set -euo pipefail # stop on any error (-e), on unset variables (-u), and on a failure inside a pipe (pipefail)

cd /opt/nyc-tlc # so Compose finds compose.yml and .env

# Image name(s) Compose resolves for `pipeline`. Only `pipeline` is pulled below
# * Follows IMAGE_TAG in .env, so a rollback pin is respected automatically.
images=$(docker compose config --images pipeline)

# For each image name, print its local ID or `missing` if it isn't on homelab yet.
image_ids() {
    # Scope `img` to function
    local img

    for img in $images; do
        docker image inspect --format '{{.Id}}' "$img" 2>/dev/null || echo "missing"
    done
}

# ---- Section: Test the local image ID of `pipeline`
# Get what is currently available local image on the machine that this script is running
before=$(image_ids)

# Name the service: a plain docker compose `pull` skips `pipeline` because of profiles: [manual].
if ! docker compose pull --quiet pipeline; then
    echo "deploy: PULL FAILED - kept current image"
    exit 1
fi
