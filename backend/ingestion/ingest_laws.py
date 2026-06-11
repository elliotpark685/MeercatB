import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.services.embedding_service import EmbeddingService
from app.services.law_ingestion_service import LawIngestionService, LawSourceArticle, LawSourceDocument


LAW_API_BASE_URL = "https://www.law.go.kr/DRF/lawService.do"


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
    def __init__(self, oc: str, base_url: str = LAW_API_BASE_URL) -> None:
        self.oc = oc
        self.base_url = base_url

    def fetch_law(self, target: TargetLaw) -> LawSourceDocument:
        params = {
            "OC": self.oc,
            "target": "law",
            "type": "JSON",
            "query": target.law_name,
        }
        source_url = f"{self.base_url}?{urlencode(params)}"
        with urlopen(source_url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return law_api_payload_to_source_document(payload=payload, target=target, source_url=source_url)


def law_api_payload_to_source_document(payload: dict[str, Any], target: TargetLaw, source_url: str) -> LawSourceDocument:
    law_body = _first_mapping(payload, ["법령", "Law", "law"]) or payload
    articles_payload = _extract_articles(law_body)
    raw_text = _extract_text(law_body)
    articles = [_payload_to_source_article(item) for item in articles_payload]
    articles = [article for article in articles if article.article_no and article.article_text]

    return LawSourceDocument(
        law_name=_first_string(law_body, ["법령명_한글", "법령명", "lawName"]) or target.law_name,
        law_short_name=target.law_short_name,
        law_type=_first_string(law_body, ["법종구분", "lawType"]) or target.law_type,
        law_no=_first_string(law_body, ["공포번호", "lawNo"]),
        source_url=source_url,
        effective_date=_first_string(law_body, ["시행일자", "effectiveDate"]),
        amendment_date=_first_string(law_body, ["공포일자", "개정일자", "amendmentDate"]),
        raw_text=raw_text,
        articles=articles or None,
    )


def _extract_articles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        payload.get("조문"),
        payload.get("조문단위"),
        payload.get("articles"),
        _first_mapping(payload, ["조문"]) or {},
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            nested = candidate.get("조문단위") or candidate.get("article")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
            if isinstance(nested, dict):
                return [nested]
    return []


def _payload_to_source_article(payload: dict[str, Any]) -> LawSourceArticle:
    article_no = _first_string(payload, ["조문번호", "조문키", "articleNo"]) or ""
    title = _first_string(payload, ["조문제목", "articleTitle"])
    article_text = _first_string(payload, ["조문내용", "조문본문", "articleText"]) or _flatten_text(payload)
    if article_no and not article_no.startswith("제"):
        article_no = f"제{article_no}조"
    return LawSourceArticle(
        article_no=article_no,
        article_title=title,
        article_text=article_text,
        effective_date=_first_string(payload, ["조문시행일자", "시행일자"]),
        status="effective",
    )


def _extract_text(payload: dict[str, Any]) -> str | None:
    text = _first_string(payload, ["원문", "본문", "rawText", "text"])
    return text.strip() if text and text.strip() else None


def _flatten_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, list):
        return "\n".join(_flatten_text(item) for item in payload if item is not None)
    if isinstance(payload, dict):
        return "\n".join(_flatten_text(value) for value in payload.values() if value is not None)
    return str(payload) if payload is not None else ""


def _first_mapping(payload: dict[str, Any], keys: list[str]) -> dict[str, Any] | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
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
