from __future__ import annotations

import json
from pathlib import Path

from domain.models import BrandCatalog, BrandDefinition, RuleConfig


class ConfigProvider:
    def __init__(
        self,
        base_path: str | Path | None = None,
        brand_catalog_path: str = "config/empresas.json",
        scoring_path: str = "config/pesos.json",
    ) -> None:
        self._base_path = Path(base_path or Path(__file__).resolve().parent.parent)
        self._brand_catalog_path = self._base_path / brand_catalog_path
        self._scoring_path = self._base_path / scoring_path

    def load_brand_catalog(self) -> BrandCatalog:
        data = self._read_json(self._brand_catalog_path)
        brands: dict[str, BrandDefinition] = {}

        for brand_data in data.get("brands", []):
            brand = BrandDefinition(
                brand_id=brand_data["brand_id"],
                display_name=brand_data["display_name"],
                sector=brand_data["sector"],
                official_domains=tuple(brand_data.get("official_domains", [])),
                official_tlds=tuple(brand_data.get("official_tlds", [])),
                primary_keywords=tuple(brand_data.get("primary_keywords", [])),
                secondary_keywords=tuple(brand_data.get("secondary_keywords", [])),
                related_keywords=tuple(brand_data.get("related_keywords", [])),
                typosquatting_variants=tuple(
                    brand_data.get("typosquatting_variants", [])
                ),
            )
            brands[brand.brand_id] = brand

        return BrandCatalog(version=data.get("version", "1.0"), brands=brands)

    def load_scoring_config(self) -> dict[str, object]:
        data = self._read_json(self._scoring_path)
        rules = tuple(
            RuleConfig(
                rule_id=rule["rule_id"],
                name=rule["name"],
                condition=rule["condition"],
                weight=int(rule["weight"]),
                enabled=bool(rule.get("enabled", True)),
                description=rule.get("description", ""),
                references=tuple(rule.get("references", [])),
                parameters=rule.get("parameters", {}),
            )
            for rule in data.get("rules", [])
        )

        return {
            "analysis_timeout_seconds": float(
                data.get("analysis_timeout_seconds", 10.0)
            ),
            "content_timeout_seconds": float(data.get("content_timeout_seconds", 2.0)),
            "thresholds": data.get(
                "thresholds", {"medium": 40, "high": 70, "unknown_on_errors": True}
            ),
            "suspicious_tlds": set(data.get("suspicious_tlds", [])),
            "social_engineering_keywords": set(
                data.get("social_engineering_keywords", [])
            ),
            "compound_tlds": set(data.get("compound_tlds", [])),
            "anomalous_length_threshold": int(
                data.get("anomalous_length_threshold", 32)
            ),
            "deceptive_subdomain_threshold": int(
                data.get("deceptive_subdomain_threshold", 2)
            ),
            "alert_threshold": int(data.get("alert_threshold", 70)),
            "rules": rules,
        }

    def _read_json(self, path: Path) -> dict[str, object]:
        with path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
