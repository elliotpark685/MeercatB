from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python evaluation/compare.py baseline.json improved.json")
    left, right = (json.loads(Path(path).read_text(encoding="utf-8"))["metrics"] for path in sys.argv[1:])
    for key in ("hit_at_1", "hit_at_3", "hit_at_5", "mrr", "average_latency_ms"):
        delta = right[key] - left[key]
        print(f"{key:20} {left[key]:>8.3f}  {right[key]:>8.3f}  ({delta:+.3f})")


if __name__ == "__main__":
    main()
