"""Run the v0.5 TRT60 Parser PoC against a native-text PDF."""

import argparse
from pathlib import Path

from app.crane.trt60_parser import TerexTRT60Parser


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a Terex TRT60 load-chart PDF.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, help="Write deterministic canonical JSON.")
    args = parser.parse_args()
    result = TerexTRT60Parser().parse_pdf(args.pdf)
    payload = TerexTRT60Parser.to_deterministic_json(result)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
