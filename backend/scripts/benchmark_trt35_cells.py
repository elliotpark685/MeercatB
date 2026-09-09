"""Offline OCR experiment. Outputs are candidates, never engineering approval."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.crane.cell_ocr import EasyOcrCellRunner, detect_confirmed_dash
import cv2
import numpy as np
from app.crane.trt35_pipeline import Trt35Page11Pipeline
from app.crane.trt35_validation import evaluate_golden


class RecognitionReader:
    def __init__(self, reader, scale=1, padding=8):
        self.reader = reader
        self.scale = scale
        self.padding = padding

    def readtext(self, image, **kwargs):
        # Experimental recognition without the detector that can omit '1.'.
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        ink = gray < 180
        # Reject border rules from the recognition area, preserving glyphs.
        ink[ink.sum(axis=1) > gray.shape[1] * .8] = False
        yy, xx = np.where(ink)
        if not len(xx):
            return []
        x0, x1 = int(xx.min()), int(xx.max()) + 1
        y0, y1 = int(yy.min()), int(yy.max()) + 1
        if detect_confirmed_dash(image) is not None:
            return []
        tight = gray[y0:y1, x0:x1]
        padded = cv2.copyMakeBorder(tight, self.padding, self.padding, self.padding, self.padding, cv2.BORDER_CONSTANT, value=255)
        if self.scale != 1:
            padded = cv2.resize(padded, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_CUBIC)
        observations = self.reader.recognize(padded, detail=1, allowlist='0123456789.-', paragraph=False)
        box = [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
        return [(box, text, confidence) for _, text, confidence in observations]


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('pdf', type=Path)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--scales', nargs='+', type=int)
    cli.add_argument('--pads', nargs='+', type=int)
    args = cli.parse_args()
    payload = args.pdf.read_bytes()
    runner = EasyOcrCellRunner()
    reader = runner._get_reader()
    golden = json.loads((Path(__file__).resolve().parents[1] / 'evaluation/datasets/trt35_page11_100_golden.json').read_text())
    reports = {}
    engines = [(f'recognition_{s}x', EasyOcrCellRunner(RecognitionReader(reader,s))) for s in args.scales] if args.scales else [('baseline', runner), ('recognition', EasyOcrCellRunner(RecognitionReader(reader)))]
    if args.pads:
        engines = [(f'padding_{p}', EasyOcrCellRunner(RecognitionReader(reader,padding=p))) for p in args.pads]
    for name, engine in engines:
        started = time.perf_counter()
        result = Trt35Page11Pipeline().parse_page11(payload, table_bbox_pdf=(80,224,515,478), ocr_runner=lambda _: [], cell_ocr_runner=engine.read)
        reports[name] = {'seconds': time.perf_counter()-started, 'golden_subset_only': evaluate_golden(result,golden).model_dump(), 'result': result.model_dump(mode='json')}
        print(name, reports[name]['golden_subset_only'], flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reports, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
