"""Reference-only Golden Dataset loader for the TRT60 Engineering Review PoC."""

import json
from pathlib import Path


REFERENCE_FILE_HASH_SHA256 = "004427e03e8751bb0b1c956d97641305a2d3e5f51fe47f349d5bb42ec3d13210"


def load_golden_dataset() -> list[dict]:
    dataset_path = Path(__file__).parents[2] / "evaluation" / "datasets" / "trt60_golden.json"
    return json.loads(dataset_path.read_text(encoding="utf-8"))
