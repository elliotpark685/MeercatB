import json
import os
from pathlib import Path

from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import easyocr


root = Path(__file__).resolve().parent / "pdfs"
source = root / "trt35-p11-3x.png"
crop = root / "trt35-p11-top-table.png"
output = root / "trt35-p11-top-table-ocr.json"

image = Image.open(source)
image.crop((0, 420, 1550, 1550)).save(crop)
reader = easyocr.Reader(["en"], gpu=False, verbose=False)
result = reader.readtext(str(crop), detail=1, paragraph=False, allowlist="0123456789.-mtx%")
output.write_text(
    json.dumps(
        [
            {
                "text": text,
                "confidence": confidence,
                "bbox_pdf": [
                    round(box[0][0] / 3, 2),
                    round((box[0][1] + 420) / 3, 2),
                    round(box[2][0] / 3, 2),
                    round((box[2][1] + 420) / 3, 2),
                ],
            }
            for box, text, confidence in result
        ],
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
