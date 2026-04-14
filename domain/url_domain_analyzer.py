from __future__ import annotations

from application.interfaces import StaticContentFetcherPort
from domain.feature_extractor import FeatureExtractor
from domain.models import BrandCatalog, DomainInput, FeatureSet
from domain.utils import normalize_token


class URLDomainAnalyzer:
    def __init__(
        self,
        feature_extractor: FeatureExtractor,
        content_fetcher: StaticContentFetcherPort | None = None,
    ) -> None:
        self._feature_extractor = feature_extractor
        self._content_fetcher = content_fetcher

    def analyze(self, input_data: DomainInput, catalog: BrandCatalog) -> FeatureSet:
        features = self._feature_extractor.extract(input_data, catalog)

        if not input_data.enable_content_analysis or self._content_fetcher is None:
            return features

        features.content_analysis_attempted = True
        snapshot = self._content_fetcher.fetch(
            input_data.normalized_url, input_data.content_timeout_seconds
        )
        features.http_status = snapshot.status_code
        features.redirected = snapshot.redirected

        if snapshot.error_code:
            features.errors.append(snapshot.error_code)
            if snapshot.limitation:
                features.limitations.append(snapshot.limitation)
            return features

        features.content_analysis_succeeded = True
        features.content_title = snapshot.title
        features.content_excerpt = snapshot.text_excerpt

        content_text = normalize_token(
            f"{snapshot.title} {snapshot.text_excerpt} {snapshot.final_url}"
        )
        for brand in catalog.brands.values():
            brand_terms = {
                normalize_token(brand.display_name),
                *(normalize_token(keyword) for keyword in brand.primary_keywords),
            }
            if any(term and term in content_text for term in brand_terms):
                if brand.brand_id not in features.content_brand_mentions:
                    features.content_brand_mentions.append(brand.brand_id)

        if features.content_brand_mentions:
            features.evidence.append(
                "Coincidencias de marca en contenido estático: "
                + ", ".join(sorted(features.content_brand_mentions))
                + "."
            )

        return features
