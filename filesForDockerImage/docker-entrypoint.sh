#!/bin/bash
set -ue
shopt -s nullglob

export TZ=${TZ:-Asia/Tokyo}

if [ -z "${SAKURA_ARTIFACT_DIR:-}" ]; then
      	echo "Environment variable SAKURA_ARTIFACT_DIR is not set" >&2
      	exit 1
fi

if [ -z "${SAKURA_TASK_ID:-}" ]; then
      	echo "Environment variable SAKURA_TASK_ID is not set" >&2
	exit 1
fi

if [ -z "${PROMPT:-}" ]; then
      	echo "Environment variable PROMPT is not set" >&2
	exit 1
fi

pushd /FLUX2-klein-4B

python3 runner.py \
  --batch="${BATCH:-1}" \
  --height="${HEIGHT:-1024}" \
  --num="${NUM_IMAGES:-1}" \
  --output="${SAKURA_ARTIFACT_DIR}" \
  --prompt="${PROMPT}" \
  --objst-bucket="${OBJST_BUCKET:-}" \
  --objst-endpoint="${OBJST_ENDPOINT:-}" \
  --objst-secret="${OBJST_SECRET:-}" \
  --objst-token="${OBJST_TOKEN:-}" \
  --steps="${STEPS:-20}" \
  --width="${WIDTH:-1024}"
popd
