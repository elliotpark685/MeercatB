from datetime import date

from app.utils.article_title_index_loader import CanonicalArticleIndexItem
from app.utils.law_parser import parse_korean_law_articles


def test_parser_does_not_split_on_article_reference():
    text = (
        "[PAGE:1]\n"
        "제42조(추락의 방지)\n"
        "사업주는 제42조제2항 및 제38조제1항제6호 기준을 함께 지켜야 한다.\n"
        "추락위험이 있는 장소에는 안전난간을 설치한다.\n"
    )
    articles = parse_korean_law_articles(text, law_name="산업안전보건기준에 관한 규칙")
    assert len(articles) == 1
    assert "제42조제2항" in articles[0].full_text


def test_parser_skips_toc_only_entries_with_canonical_index():
    canonical = [
        CanonicalArticleIndexItem(
            article_no="제1조",
            article_title="목적",
            part=None,
            chapter="제1장 총칙",
            section=None,
            gwan=None,
            sok=None,
            order=1,
        )
    ]
    text = (
        "[PAGE:1]\n"
        "산업안전보건기준에 관한 규칙\n"
        "목차\n"
        "제1조(목적)\n"
        "[PAGE:2]\n"
        "산업안전보건기준에 관한 규칙\n"
        "제1조(목적)\n"
        "이 규칙은 산업안전보건법에 따라 필요한 사항을 정한다.\n"
    )
    articles = parse_korean_law_articles(
        text,
        law_name="산업안전보건기준에 관한 규칙",
        canonical_article_index=canonical,
        default_effective_date=date(2026, 3, 2),
    )
    assert len(articles) == 1
    assert articles[0].article_no == "제1조"
    assert articles[0].status == "effective"
    assert articles[0].effective_date == date(2026, 3, 2)


def test_duplicate_article_is_preserved():
    text = (
        "[PAGE:1]\n"
        "제1조(목적)\n"
        "본문 A\n"
        "[시행일: 2099. 1. 1.]\n"
        "[PAGE:2]\n"
        "제1조(목적)\n"
        "본문 B\n"
        "[시행일: 2000. 1. 1.]\n"
    )
    articles = parse_korean_law_articles(text, law_name="산업안전보건법")
    assert len(articles) == 2
    assert articles[0].article_no == "제1조"
    assert articles[1].article_no == "제1조"
    assert articles[0].effective_date != articles[1].effective_date
    assert articles[0].status != articles[1].status


def test_parser_keeps_single_line_article_body_and_drops_page_header_fragment():
    """Regression for the PDF page that previously lost 제30조."""
    canonical = [
        CanonicalArticleIndexItem("제29조", "천장의 높이", None, "제3장 통로", None, None, None, 29),
        CanonicalArticleIndexItem("제30조", "계단의 난간", None, "제3장 통로", None, None, None, 30),
        CanonicalArticleIndexItem("제31조", "보호구의 제한적 사용", None, "제4장 보호구", None, None, None, 31),
        CanonicalArticleIndexItem("제70조", "시스템비계의 조립 작업 시 준수사항", None, None, None, None, None, 70),
    ]
    text = (
        "[PAGE:25]\n"
        "제29조(천장의 높이) 계단 위의 공간에는 장애물이 없어야 한다.\n"
        "제30조(계단의 난간) 사업주는 높이 1미터 이상인 계단의 개방된 측면에 안전난간을 설치하여야 한다.\n"
        "제4장 보호구\n"
        "제31조(보호구의 제한적 사용) 사업주는 필요한 경우에만 보호구를 사용하도록 하여야 한다.\n"
        "[PAGE:3]\n"
        "제70조(시스템비계의 조립 작업 시 준수사항)\n"
        "법제처                                                            3                                                       국가법령정보센터\n"
        "산업안전보건기준에 관한 규칙\n"
        "제71조(시스템비계의 재료) 본문\n"
    )

    articles = parse_korean_law_articles(
        text,
        law_name="산업안전보건기준에 관한 규칙",
        canonical_article_index=canonical,
    )
    by_no = {article.article_no: article for article in articles}

    assert {"제29조", "제30조", "제31조"}.issubset(by_no)
    assert by_no["제30조"].article_title == "계단의 난간"
    assert "안전난간" in by_no["제30조"].full_text
    assert "제70조" not in by_no
