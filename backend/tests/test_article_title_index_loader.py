from pathlib import Path
import uuid

from app.utils.article_title_index_loader import load_article_title_index


def test_parse_article_title_index_with_ui2_cases():
    sample = (
        "제1편 총칙\n"
        "제1장 공통기준\n"
        "제1조(목적)\n"
        "제4조의2(분진의 흩날림 방지)\n"
        "제221조의2(충돌위험 방지조치)\n"
    )
    tmp_dir = Path("tests/.tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    index_file = tmp_dir / f"index_{uuid.uuid4().hex}.txt"
    index_file.write_text(sample, encoding="utf-8")

    items = load_article_title_index(str(index_file))
    assert len(items) == 3
    assert items[1].article_no == "제4조의2"
    assert items[1].article_title == "분진의 흩날림 방지"
    assert items[2].article_no == "제221조의2"
    assert items[2].article_title == "충돌위험 방지조치"
    assert items[0].chapter == "제1장 공통기준"
