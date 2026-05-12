from __future__ import annotations

from .collector import FETCHERS
from .models import Company


def validate_companies(companies: list[Company]) -> list[dict]:
    issues: list[dict] = []
    seen_slugs: set[str] = set()

    for company in companies:
        if company.slug in seen_slugs:
            issues.append(
                {
                    "severity": "error",
                    "code": "duplicate_company_slug",
                    "company_slug": company.slug,
                    "message": f"duplicate company slug: {company.slug}",
                }
            )
        seen_slugs.add(company.slug)

        if not company.sources:
            issues.append(
                {
                    "severity": "warning",
                    "code": "missing_sources",
                    "company_slug": company.slug,
                    "message": f"{company.slug} has no configured sources",
                }
            )

        for source in company.sources:
            if not source.url.strip():
                issues.append(
                    {
                        "severity": "error",
                        "code": "missing_source_url",
                        "company_slug": company.slug,
                        "source_label": source.label or source.kind,
                        "message": f"{company.slug}/{source.label or source.kind} is missing a source url",
                    }
                )
            if source.kind not in FETCHERS:
                issues.append(
                    {
                        "severity": "error",
                        "code": "unsupported_source_kind",
                        "company_slug": company.slug,
                        "source_label": source.label or source.kind,
                        "message": f"{company.slug}/{source.label or source.kind} uses unsupported source kind {source.kind}",
                    }
                )
            if source.require_published_at and not source.fetch_article_details and source.kind == "html":
                issues.append(
                    {
                        "severity": "warning",
                        "code": "published_at_requires_article_details",
                        "company_slug": company.slug,
                        "source_label": source.label or source.kind,
                        "message": (
                            f"{company.slug}/{source.label or source.kind} requires published_at "
                            "but article details fetching is disabled"
                        ),
                    }
                )
    return issues


def build_source_diagnostics(companies: list[Company]) -> list[dict]:
    diagnostics: list[dict] = []
    for company in companies:
        for source in company.sources:
            issues: list[str] = []
            severity = "ok"
            suggestion = ""
            if not source.url.strip():
                issues.append("missing_source_url")
                severity = "error"
                suggestion = "fill in the official source url before enabling this source"
            if source.kind not in FETCHERS:
                issues.append("unsupported_source_kind")
                severity = "error"
                suggestion = "switch this source to rss, atom, or html"
            if source.require_published_at and not source.fetch_article_details and source.kind == "html":
                issues.append("published_at_requires_article_details")
                if severity != "error":
                    severity = "warning"
                suggestion = "enable article detail fetching so published_at can be extracted reliably"
            if severity == "ok" and source.kind == "html" and source.fetch_article_details and source.detail_fetch_limit < 4:
                suggestion = "consider raising detail_fetch_limit if this source frequently returns zero matched entries"
            diagnostics.append(
                {
                    "company_slug": company.slug,
                    "company_name": company.name,
                    "source_label": source.label or source.kind,
                    "source_kind": source.kind,
                    "source_url": source.url,
                    "severity": severity,
                    "issues": issues,
                    "suggestion": suggestion,
                }
            )
    return diagnostics
