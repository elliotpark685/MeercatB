from app.services.query_analyzer import QueryAnalyzer


def test_query_analyzer_detects_bige_and_fall():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("비계 작업 중 추락 방지 설치 기준 알려줘")
    assert "비계" in result.work_types
    assert "추락" in result.risk_types


def test_query_analyzer_detects_excavation_and_collapse():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("굴착 작업 붕괴 예방 점검 항목이 뭐야?")
    assert "굴착" in result.work_types
    assert "붕괴" in result.risk_types

