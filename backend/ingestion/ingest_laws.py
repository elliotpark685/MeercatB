import argparse
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.services.embedding_service import EmbeddingService
from app.services.law_ingestion_service import LawIngestionService, LawSourceDocument


LAW_API_BASE_URL = "https://www.law.go.kr/DRF/lawService.do"
LAW_API_SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"


@dataclass(frozen=True)
class TargetLaw:
    law_name: str
    law_short_name: str
    law_type: str = "법률"


TARGET_LAWS = [
    TargetLaw("산업안전보건법", "산안법"),
    TargetLaw("시설물의 안전 및 유지관리에 관한 특별법", "시설물안전법"),
    TargetLaw("건설산업기본법", "건산법"),
    TargetLaw("건설기술 진흥법", "건설기술진흥법"),
    TargetLaw("중대재해 처벌 등에 관한 법률", "중대재해처벌법"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Korean law text into DB.")
    parser.add_argument("--all-target-laws", action="store_true", help="Ingest the five built-in target laws.")
    parser.add_argument("--prefer-local", action="store_true", help="Use local fallback files before Open API.")
    parser.add_argument("--fallback-dir", default="data/raw/laws", help="Directory containing local PDF/TXT fallback files.")
    parser.add_argument("--law-api-oc", default=settings.law_api_oc, help="Law API OC key. Defaults to LAW_API_OC.")
    parser.add_argument("--file-path", required=False, help="Path to a single PDF/TXT law file.")
    parser.add_argument(
        "--article-title-index-path",
        required=False,
        default=None,
        help="Optional path to article-title canonical TXT index for single-file ingestion.",
    )
    parser.add_argument("--law-name", required=False, help="Law name for single-file ingestion.")
    parser.add_argument("--law-short-name", required=False, default=None, help="Optional short law name.")
    parser.add_argument("--law-type", required=False, default=None, help="Law type, e.g. 법률 or 부령.")
    parser.add_argument("--law-no", required=False, default=None, help="Law number.")
    parser.add_argument("--effective-date", required=False, default=None, help="Document effective date in YYYY-MM-DD.")
    parser.add_argument("--amendment-date", required=False, default=None, help="Document amendment date in YYYY-MM-DD.")
    parser.add_argument("--source-url", required=False, default=None, help="Source URL for single-file ingestion.")
    return parser.parse_args()


class LawOpenApiClient:
    def __init__(
        self,
        oc: str,
        base_url: str = LAW_API_BASE_URL,
        search_url: str = LAW_API_SEARCH_URL,
    ) -> None:
        self.oc = oc
        self.base_url = base_url
        self.search_url = search_url

    def _find_law_serial_number(self, law_name: str) -> str | None:
        params = {"OC": self.oc, "target": "law", "type": "JSON", "query": law_name}
        url = f"{self.search_url}?{urlencode(params)}"
        with urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

        laws = (payload.get("LawSearch") or {}).get("law") or []
        if isinstance(laws, dict):
            laws = [laws]

        for item in laws:
            if isinstance(item, dict) and item.get("법령명한글", "").strip() == law_name:
                return item.get("법령일련번호")
        if laws and isinstance(laws[0], dict):
            return laws[0].get("법령일련번호")
        return None

    def fetch_law(self, target: TargetLaw) -> LawSourceDocument:
        mst = self._find_law_serial_number(target.law_name)
        if not mst:
            raise ValueError(f"Law not found via Open API search: {target.law_name}")

        params = {"OC": self.oc, "target": "law", "MST": mst, "type": "JSON"}
        source_url = f"{self.base_url}?{urlencode(params)}"
        with urlopen(source_url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return law_api_payload_to_source_document(payload=payload, target=target, source_url=source_url)


def law_api_payload_to_source_document(payload: dict[str, Any], target: TargetLaw, source_url: str) -> LawSourceDocument:
    law_body = payload.get("법령") or payload.get("Law") or payload
    basic_info = law_body.get("기본정보") or {}

    raw_text = _reconstruct_law_text(law_body)
    if not raw_text.strip():
        raise ValueError(f"No article content returned for {target.law_name}")

    return LawSourceDocument(
        law_name=_first_string(basic_info, ["법령명_한글"]) or target.law_name,
        law_short_name=target.law_short_name,
        law_type=_dict_content(basic_info.get("법종구분")) or target.law_type,
        law_no=_first_string(basic_info, ["공포번호"]),
        source_url=source_url,
        effective_date=_first_string(basic_info, ["시행일자"]),
        amendment_date=_first_string(basic_info, ["공포일자"]),
        raw_text=raw_text,
        articles=None,
    )


ARTICLE_CONTENT_SPLIT_RE = re.compile(r"^\s*((?:제\d+조(?:의\d+)?)(?:\([^)]*\))?)\s*(.*)$")


def _reconstruct_law_text(law_body: dict[str, Any]) -> str:
    """Flatten the 법제처 Open API 조문 tree into PDF-like article text.

    `parse_korean_law_articles` expects line-by-line text where article/chapter
    headers start their own line, so this mirrors that shape from the JSON tree.
    Article headers (e.g. "제1조(목적) 이 법은 ...") are split onto their own
    line from the body text, because `parse_korean_law_articles` drops any
    article whose header line has no following body line.
    """
    units = _as_list((law_body.get("조문") or {}).get("조문단위"))

    lines: list[str] = []
    for unit in units:
        if not isinstance(unit, dict):
            continue
        content = _text_content(unit.get("조문내용"))
        is_article = unit.get("조문여부") == "조문"
        if content:
            if is_article:
                match = ARTICLE_CONTENT_SPLIT_RE.match(content)
                if match and match.group(2).strip():
                    lines.append(match.group(1))
                    lines.append(match.group(2).strip())
                else:
                    lines.append(content)
            else:
                lines.append(content)
        if not is_article:
            continue
        for hang in _as_list(unit.get("항")):
            _append_hang_lines(lines, hang)
        for ho in _as_list(unit.get("호")):
            _append_ho_lines(lines, ho)
    return "\n".join(lines)


def _append_hang_lines(lines: list[str], hang: Any) -> None:
    if not isinstance(hang, dict):
        return
    content = _text_content(hang.get("항내용"))
    if content:
        lines.append(content)
    for ho in _as_list(hang.get("호")):
        _append_ho_lines(lines, ho)


def _append_ho_lines(lines: list[str], ho: Any) -> None:
    if not isinstance(ho, dict):
        return
    content = _text_content(ho.get("호내용"))
    if content:
        lines.append(content)
    for mok in _as_list(ho.get("목")):
        if isinstance(mok, dict):
            content = _text_content(mok.get("목내용"))
            if content:
                lines.append(content)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text_content(value: Any) -> str | None:
    """Normalize a 조문/항/호/목 *내용 value into a single text block.

    The Open API usually returns these as plain strings, but for amended
    articles it can return nested lists of strings (e.g. body text plus a
    trailing [시행일] note). Flatten any nesting into newline-joined text.
    """
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, list):
        parts = [_text_content(item) for item in value]
        parts = [part for part in parts if part]
        return "\n".join(parts) if parts else None
    if isinstance(value, dict):
        return _text_content(value.get("content"))
    return None


def _dict_content(value: Any) -> str | None:
    if isinstance(value, dict):
        content = value.get("content")
        return content.strip() if isinstance(content, str) else None
    if isinstance(value, str):
        return value.strip() or None
    return None


def _first_string(payload: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def find_local_fallback_file(fallback_dir: str, target: TargetLaw) -> Path | None:
    root = Path(fallback_dir)
    if not root.exists():
        return None
    candidates = []
    for suffix in ("*.txt", "*.pdf"):
        candidates.extend(root.glob(suffix))
    names = [target.law_name, target.law_short_name]
    for path in sorted(candidates):
        normalized = path.stem.replace("_", "").replace(" ", "")
        if any(name and name.replace(" ", "") in normalized for name in names):
            return path
    return None


def ingest_target_law(
    service: LawIngestionService,
    target: TargetLaw,
    api_client: LawOpenApiClient | None,
    fallback_dir: str,
    prefer_local: bool,
) -> dict:
    fallback_file = find_local_fallback_file(fallback_dir, target)

    if prefer_local and fallback_file is not None:
        return service.ingest_file(
            file_path=str(fallback_file),
            law_name=target.law_name,
            law_short_name=target.law_short_name,
            law_type=target.law_type,
            source_url=str(fallback_file),
        )

    if api_client is not None:
        try:
            source = api_client.fetch_law(target)
            return service.ingest_source_document(source)
        except Exception as exc:
            if fallback_file is None:
                return {"law_name": target.law_name, "status": "failed", "error": str(exc)}
            fallback_result = service.ingest_file(
                file_path=str(fallback_file),
                law_name=target.law_name,
                law_short_name=target.law_short_name,
                law_type=target.law_type,
                source_url=str(fallback_file),
            )
            fallback_result["fallback_reason"] = str(exc)
            return fallback_result

    if fallback_file is None:
        return {"law_name": target.law_name, "status": "failed", "error": "No API key and no local fallback file"}

    return service.ingest_file(
        file_path=str(fallback_file),
        law_name=target.law_name,
        law_short_name=target.law_short_name,
        law_type=target.law_type,
        source_url=str(fallback_file),
    )


def main() -> None:
    args = parse_args()
    init_db()
    db = SessionLocal()
    try:
        service = LawIngestionService(db=db, embedding_service=EmbeddingService())
        if args.all_target_laws:
            api_client = LawOpenApiClient(args.law_api_oc) if args.law_api_oc and not args.prefer_local else None
            results = [
                ingest_target_law(
                    service=service,
                    target=target,
                    api_client=api_client,
                    fallback_dir=args.fallback_dir,
                    prefer_local=args.prefer_local,
                )
                for target in TARGET_LAWS
            ]
            for result in results:
                print(json.dumps(result, ensure_ascii=False))
            return

        if not args.file_path or not args.law_name:
            raise SystemExit("--file-path and --law-name are required unless --all-target-laws is set.")

        summary = service.ingest_file(
            file_path=args.file_path,
            law_name=args.law_name,
            law_short_name=args.law_short_name,
            law_type=args.law_type,
            law_no=args.law_no,
            effective_date=args.effective_date,
            amendment_date=args.amendment_date,
            source_url=args.source_url,
            article_title_index_path=args.article_title_index_path,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
