# copyright github
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
DATA=${1:?"Usage: $0 path/to/ner.jsonl"}
OUT_DIR=${2:-"$ROOT/models/ner/$(date +%Y%m%d_%H%M%S)"}

python "$ROOT/app/training/train_ner.py" --data "$DATA" --out "$OUT_DIR"
echo "$OUT_DIR"
