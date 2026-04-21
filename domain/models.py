from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DomainInput:
    original_value: str
    normalized_url: str
    normalized_domain: str
    scheme: str
    path: str = ""
    source: str = "manual"
    enable_content_analysis: bool = True
    analysis_timeout_seconds: float = 10.0
    content_timeout_seconds: float = 2.0
    run_id: str = "manual"


@dataclass(frozen=True)
class BrandDefinition:
    brand_id: str
    display_name: str
    sector: str
    official_domains: tuple[str, ...]
    official_tlds: tuple[str, ...]
    primary_keywords: tuple[str, ...]
    secondary_keywords: tuple[str, ...]
    related_keywords: tuple[str, ...]
    typosquatting_variants: tuple[str, ...] = ()


@dataclass(frozen=True)
class BrandCatalog:
    version: str
    brands: dict[str, BrandDefinition]


@dataclass
class StaticContentSnapshot:
    requested_url: str
    final_url: str = ""
    status_code: int | None = None
    title: str = ""
    text_excerpt: str = ""
    redirected: bool = False
    error_code: str | None = None
    limitation: str | None = None


@dataclass
class FeatureSet:
    normalized_url: str
    normalized_domain: str
    registrable_domain: str
    tld: str
    domain_length: int
    url_length: int
    subdomains: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    matched_brand_ids: list[str] = field(default_factory=list)
    matched_official_domains: list[str] = field(default_factory=list)
    matched_primary_keywords: list[str] = field(default_factory=list)
    matched_secondary_keywords: list[str] = field(default_factory=list)
    matched_related_keywords: list[str] = field(default_factory=list)
    social_engineering_terms: list[str] = field(default_factory=list)
    typosquatting_matches: list[str] = field(default_factory=list)
    brand_stuffing_matches: list[str] = field(default_factory=list)
    suspicious_subdomain_tokens: list[str] = field(default_factory=list)
    content_brand_mentions: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exact_brand_match: bool = False
    suspicious_tld: bool = False
    anomalous_length: bool = False
    deceptive_subdomain: bool = False
    content_analysis_attempted: bool = False
    content_analysis_succeeded: bool = False
    http_status: int | None = None
    redirected: bool = False
    content_title: str = ""
    content_excerpt: str = ""

    def has_structural_signal(self) -> bool:
        return any(
            [
                self.exact_brand_match,
                bool(self.matched_brand_ids),
                bool(self.matched_primary_keywords),
                bool(self.matched_secondary_keywords),
                bool(self.matched_related_keywords),
                bool(self.social_engineering_terms),
                bool(self.typosquatting_matches),
                bool(self.brand_stuffing_matches),
                self.suspicious_tld,
                self.anomalous_length,
                self.deceptive_subdomain,
            ]
        )


@dataclass(frozen=True)
class RuleConfig:
    rule_id: str
    name: str
    condition: str
    weight: int
    enabled: bool = True
    description: str = ""
    references: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    name: str
    condition: str
    weight: int
    evidence: tuple[str, ...]
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScoreResult:
    total_score: int
    matched_rules: tuple[RuleMatch, ...]


@dataclass(frozen=True)
class ExplanationResult:
    score: int
    risk_level: RiskLevel
    triggered_rules: tuple[RuleMatch, ...]
    evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "risk_level": self.risk_level.value,
            "triggered_rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "condition": rule.condition,
                    "weight": rule.weight,
                    "evidence": list(rule.evidence),
                    "references": list(rule.references),
                }
                for rule in self.triggered_rules
            ],
            "evidence": list(self.evidence),
            "limitations": list(self.limitations),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class AnalysisResult:
    input_value: str
    normalized_domain: str
    risk_level: RiskLevel
    score: int
    status: str
    score_breakdown: ScoreResult
    explanation: ExplanationResult
    features: FeatureSet
    matched_brands: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    execution_time_ms: int = 0
    analyzed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    run_id: str = "manual"

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_value": self.input_value,
            "normalized_domain": self.normalized_domain,
            "risk_level": self.risk_level.value,
            "score": self.score,
            "status": self.status,
            "matched_brands": list(self.matched_brands),
            "limitations": list(self.limitations),
            "errors": list(self.errors),
            "execution_time_ms": self.execution_time_ms,
            "analyzed_at": self.analyzed_at,
            "run_id": self.run_id,
            "score_breakdown": {
                "total_score": self.score_breakdown.total_score,
                "matched_rules": [
                    {
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "condition": rule.condition,
                        "weight": rule.weight,
                        "evidence": list(rule.evidence),
                        "references": list(rule.references),
                    }
                    for rule in self.score_breakdown.matched_rules
                ],
            },
            "features": {
                "normalized_url": self.features.normalized_url,
                "normalized_domain": self.features.normalized_domain,
                "registrable_domain": self.features.registrable_domain,
                "tld": self.features.tld,
                "domain_length": self.features.domain_length,
                "url_length": self.features.url_length,
                "subdomains": list(self.features.subdomains),
                "tokens": list(self.features.tokens),
                "matched_brand_ids": list(self.features.matched_brand_ids),
                "matched_official_domains": list(self.features.matched_official_domains),
                "matched_primary_keywords": list(
                    self.features.matched_primary_keywords
                ),
                "matched_secondary_keywords": list(
                    self.features.matched_secondary_keywords
                ),
                "matched_related_keywords": list(
                    self.features.matched_related_keywords
                ),
                "social_engineering_terms": list(
                    self.features.social_engineering_terms
                ),
                "typosquatting_matches": list(self.features.typosquatting_matches),
                "brand_stuffing_matches": list(
                    self.features.brand_stuffing_matches
                ),
                "suspicious_subdomain_tokens": list(
                    self.features.suspicious_subdomain_tokens
                ),
                "content_brand_mentions": list(self.features.content_brand_mentions),
                "evidence": list(self.features.evidence),
                "limitations": list(self.features.limitations),
                "errors": list(self.features.errors),
                "exact_brand_match": self.features.exact_brand_match,
                "suspicious_tld": self.features.suspicious_tld,
                "anomalous_length": self.features.anomalous_length,
                "deceptive_subdomain": self.features.deceptive_subdomain,
                "content_analysis_attempted": self.features.content_analysis_attempted,
                "content_analysis_succeeded": self.features.content_analysis_succeeded,
                "http_status": self.features.http_status,
                "redirected": self.features.redirected,
                "content_title": self.features.content_title,
                "content_excerpt": self.features.content_excerpt,
            },
            "explanation": self.explanation.to_dict(),
        }


@dataclass(frozen=True)
class AISummaryResult:
    narrative_summary: str
    suggested_steps: tuple[str, ...]
    disclaimer: str
    provider: str
    model: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "narrative_summary": self.narrative_summary,
            "suggested_steps": list(self.suggested_steps),
            "disclaimer": self.disclaimer,
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class AlertDraft:
    input_value: str
    normalized_domain: str
    score: int
    risk_level: RiskLevel
    matched_brands: tuple[str, ...]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_value": self.input_value,
            "normalized_domain": self.normalized_domain,
            "score": self.score,
            "risk_level": self.risk_level.value,
            "matched_brands": list(self.matched_brands),
            "message": self.message,
        }
