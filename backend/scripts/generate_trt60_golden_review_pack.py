"""Create a human-review PDF for the TRT60 Golden Dataset acceptance gate."""

from __future__ import annotations

import argparse
import json
from io import BytesIO
from pathlib import Path

import fitz
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.crane.trt60_parser import TerexTRT60Parser

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 40


def _ascii(value: object) -> str:
    return str(value).replace("°", " deg").encode("ascii", "backslashreplace").decode("ascii")


def _draw_entry(pdf: canvas.Canvas, *, top: float, index: int, expected: dict, cell, page) -> float:
    section_height = 330
    left = MARGIN
    pdf.setFillColor(HexColor("#132238"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left, top, f"Golden {index:02d} - PDF page {expected['chart_source_page']}")
    pdf.setFillColor(HexColor("#202020"))
    pdf.setFont("Helvetica", 9)
    status = expected["cell_status"]
    expected_capacity = "N/A" if expected["rated_capacity_t"] is None else f"{expected['rated_capacity_t']} t"
    outrigger_percent = "n/a" if expected["outrigger_percent"] is None else f"{expected['outrigger_percent']}%"
    outrigger_width = "n/a" if expected["outrigger_width_m"] is None else f"{expected['outrigger_width_m']} m"
    details = [
        f"Configuration: {expected['support_mode']} / counterweight {expected['counterweight_t']} t / outrigger {outrigger_percent} / width {outrigger_width} / area {_ascii(expected['working_area'])}",
        f"Expected: radius {expected['radius_m']} m / boom {expected['boom_length_m']} m / capacity {expected_capacity} / status {status}",
        f"Evidence: source page {cell.source.source_page} / bbox {tuple(round(value, 2) for value in cell.source.source_bbox or ())} / source text {_ascii(cell.source.source_text)!r}",
        "Reviewer check: [ ] configuration  [ ] axes  [ ] capacity/status  [ ] source location",
    ]
    text = pdf.beginText(left, top - 18)
    text.setLeading(13)
    for line in details:
        text.textLine(line)
    pdf.drawText(text)

    bbox = fitz.Rect(cell.source.source_bbox)
    clip = fitz.Rect(max(0, bbox.x0 - 75), max(0, bbox.y0 - 45), min(page.rect.width, bbox.x1 + 75), min(page.rect.height, bbox.y1 + 45))
    pix = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=clip, alpha=False)
    image_bytes = BytesIO(pix.tobytes("png"))
    image = ImageReader(image_bytes)
    image_width = 430
    image_height = image_width * clip.height / clip.width
    image_x = left
    image_y = top - 75 - image_height
    pdf.drawImage(image, image_x, image_y, width=image_width, height=image_height, preserveAspectRatio=True, mask="auto")

    pdf.setStrokeColor(HexColor("#D62828"))
    pdf.setLineWidth(1.8)
    target_x = image_x + (bbox.x0 - clip.x0) / clip.width * image_width
    target_y = image_y + image_height - (bbox.y1 - clip.y0) / clip.height * image_height
    target_width = bbox.width / clip.width * image_width
    target_height = bbox.height / clip.height * image_height
    pdf.rect(target_x, target_y, target_width, target_height, stroke=1, fill=0)
    return top - section_height


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the TRT60 Golden Dataset human review pack.")
    parser.add_argument("pdf", type=Path, help="Reference TRT60 PDF")
    parser.add_argument("--output", type=Path, default=Path("output/pdf/TRT60_Golden_Review_Pack.pdf"))
    args = parser.parse_args()

    dataset_path = Path(__file__).parents[1] / "evaluation" / "datasets" / "trt60_golden.json"
    golden = json.loads(dataset_path.read_text(encoding="utf-8"))
    parsed = TerexTRT60Parser().parse_pdf(args.pdf)
    charts = {chart.source.source_page: chart for chart in parsed.load_charts}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open(args.pdf)
    pdf = canvas.Canvas(str(args.output), pagesize=A4)
    pdf.setTitle("TRT60 Golden Dataset Human Review Pack")
    for offset in range(0, len(golden), 2):
        pdf.setFont("Helvetica-Bold", 16)
        pdf.setFillColor(HexColor("#132238"))
        pdf.drawString(MARGIN, PAGE_HEIGHT - MARGIN, "TRT60 Golden Dataset - Human Review")
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(HexColor("#202020"))
        pdf.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN, f"Items {offset + 1}-{min(offset + 2, len(golden))} of {len(golden)}")
        top = PAGE_HEIGHT - MARGIN - 30
        for index, expected in enumerate(golden[offset : offset + 2], start=offset + 1):
            chart = charts[expected["chart_source_page"]]
            cell = next(item for item in chart.cells if item.radius_m == expected["radius_m"] and item.boom_length_m == expected["boom_length_m"])
            top = _draw_entry(pdf, top=top, index=index, expected=expected, cell=cell, page=document[expected["chart_source_page"] - 1])
        pdf.setFont("Helvetica", 8)
        pdf.drawString(MARGIN, 22, "Acceptance: verify each item directly against the original PDF, then sign the completion record.")
        pdf.showPage()
    pdf.save()
    document.close()
    print(args.output.resolve())


if __name__ == "__main__":
    main()
