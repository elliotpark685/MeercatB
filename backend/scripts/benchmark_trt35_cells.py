"""Offline OCR experiment. Outputs are candidates, never engineering approval."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.crane.cell_ocr import EasyOcrCellRunner, TightCropEasyOcrCellRunner
from app.crane.trt35_pipeline import Trt35Page11Pipeline
from app.crane.trt35_validation import evaluate_golden


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('pdf', type=Path)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    payload = args.pdf.read_bytes()
    runner = EasyOcrCellRunner()
    golden = json.loads((Path(__file__).resolve().parents[1] / 'evaluation/datasets/trt35_page11_100_golden.json').read_text())
    reports = {}
    engines = [
        ('baseline', runner, '0.1.0-slice'),
        ('tight_crop_recognition', TightCropEasyOcrCellRunner(), '0.1.1-tight-crop-candidate'),
    ]
    for name, engine, parser_version in engines:
        started = time.perf_counter()
        result = Trt35Page11Pipeline().parse_page11(
            payload,
            table_bbox_pdf=(80, 224, 515, 478),
            ocr_runner=lambda _: [],
            cell_ocr_runner=engine.read,
            parser_version=parser_version,
        )
        reports[name] = {'seconds': time.perf_counter()-started, 'golden_subset_only': evaluate_golden(result,golden).model_dump(), 'result': result.model_dump(mode='json')}
        print(name, reports[name]['golden_subset_only'], flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reports, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
