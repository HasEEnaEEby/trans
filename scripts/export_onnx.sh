# copyright github

set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
MODEL_DIR=${1:?"Usage: $0 path/to/models"}
OUT_DIR=${2:-"$ROOT/onnx"}

python "$ROOT/app/training/export_onnx.py" --model_dir "$MODEL_DIR" --out "$OUT_DIR"
echo "$OUT_DIR"}
