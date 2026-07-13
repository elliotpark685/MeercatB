from app.utils.law_amendment import extract_amendment_type, prepend_amendment_marker


def test_extracts_document_amendment_marker_from_header():
    raw_text = "[시행 2026. 3. 2.] [고용노동부령 제450호, 2025. 9. 1., 일부개정]\n제1조"
    assert extract_amendment_type(raw_text) == "일부개정"


def test_extracts_enactment_marker_from_header():
    assert extract_amendment_type("[법률 제1호, 1948. 7. 17., 제정]") == "제정"


def test_prepends_api_marker_when_source_has_no_header():
    assert prepend_amendment_marker("제1조", "전부개정").startswith("[제개정구분: 전부개정]")
