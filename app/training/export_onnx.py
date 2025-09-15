import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Placeholder: create dummy ONNX files
    (out / "intent.onnx").write_bytes(b"onnx-intent")
    (out / "ner.onnx").write_bytes(b"onnx-ner")
    print("Exported ONNX to:", out)


if __name__ == "__main__":
    main()
