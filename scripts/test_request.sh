# copyright github
set -euo pipefail
IMG_PATH=${1:-}
if [[ -z "$IMG_PATH" ]]; then
  echo "Usage: $0 path/to/image.jpg" >&2
  exit 1
fi

curl -s -X POST "http://localhost:8000/v1/process-magazine" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@${IMG_PATH}" \
  -F "target_language=en" | jq
