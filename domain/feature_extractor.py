from __future__ import annotations

import re

from domain.models import BrandCatalog, DomainInput, FeatureSet
from domain.utils import (
    collapse_text,
    extract_domain_label,
    extract_registrable_domain,
    looks_like_typosquatting,
    normalize_token,
    split_subdomains,
    tokenize_text,
)


class FeatureExtractor:
    def __init__(self, settings: dict[str, object]) -> None:
        self._settings = settings
        self._compound_tlds = set(settings.get("compound_tlds", set()))
        self._social_terms = {
            normalize_token(term)
            for term in settings.get("social_engineering_keywords", set())
        }
        self._suspicious_tlds = {
            normalize_token(term) for term in settings.get("suspicious_tlds", set())
        }
        self._anomalous_length_threshold = int(
            settings.get("anomalous_length_threshold", 32)
        )
        self._deceptive_subdomain_threshold = int(
            settings.get("deceptive_subdomain_threshold", 2)
        )

    def extract(self, input_data: DomainInput, catalog: BrandCatalog) -> FeatureSet:
        registrable_domain, tld = extract_registrable_domain(
            input_data.normalized_domain, self._compound_tlds
        )
        subdomains = split_subdomains(input_data.normalized_domain, registrable_domain)
        url_tokens = tokenize_text(
            f"{input_data.normalized_domain} {input_data.path.replace('/', ' ')}"
        )
        label = extract_domain_label(registrable_domain, tld)
        raw_label_segments = [
            segment for segment in re.split(r"[^a-z0-9]+", label.lower()) if segment
        ]
        collapsed_label_candidates = {
            collapsed
            for collapsed in {
                collapse_text(label),
                *(collapse_text(segment) for segment in raw_label_segments),
            }
            if collapsed
        }

        features = FeatureSet(
            normalized_url=input_data.normalized_url,
            normalized_domain=input_data.normalized_domain,
            registrable_domain=registrable_domain,
            tld=tld,
            domain_length=len(registrable_domain),
            url_length=len(input_data.normalized_url),
            subdomains=subdomains,
            tokens=url_tokens,
        )

        if len(registrable_domain) >= self._anomalous_length_threshold:
            features.anomalous_length = True
            features.evidence.append(
                f"Longitud del dominio {len(registrable_domain)} >= {self._anomalous_length_threshold}."
            )

        if normalize_token(tld) in self._suspicious_tlds:
            features.suspicious_tld = True
            features.evidence.append(f"TLD sospechoso detectado: {tld}.")

        features.social_engineering_terms.extend(
            sorted(term for term in set(url_tokens) if term in self._social_terms)
        )
        if features.social_engineering_terms:
            features.evidence.append(
                "Terminos de ingenieria social detectados: "
                + ", ".join(features.social_engineering_terms)
                + "."
            )

        brand_tokens_in_subdomains: set[str] = set()

        for brand in catalog.brands.values():
            official_matches = [
                official
                for official in brand.official_domains
                if normalize_token(registrable_domain) == normalize_token(official)
            ]
            if official_matches:
                features.exact_brand_match = True
                features.matched_brand_ids.append(brand.brand_id)
                features.matched_official_domains.extend(official_matches)
                features.evidence.append(
                    f"Coincidencia exacta con dominio oficial de {brand.display_name}."
                )
                continue

            primary_keywords = {
                normalize_token(keyword) for keyword in brand.primary_keywords
            }
            secondary_keywords = {
                normalize_token(keyword) for keyword in brand.secondary_keywords
            }
            related_keywords = {
                normalize_token(keyword) for keyword in brand.related_keywords
            }
            raw_typo_variants = {
                variant.lower() for variant in brand.typosquatting_variants
            }
            typo_variants = {
                normalize_token(variant) for variant in brand.typosquatting_variants
            }
            collapsed_primary_keyword_map = self._build_collapsed_keyword_map(
                brand.primary_keywords
            )
            keyword_tokens = self._extract_keyword_tokens(brand)
            official_labels = self._extract_official_labels(brand)

            matched_primary = sorted(primary_keywords.intersection(url_tokens))
            matched_secondary = sorted(secondary_keywords.intersection(url_tokens))
            matched_related = sorted(related_keywords.intersection(url_tokens))
            embedded_primary, brand_stuffing_matches = (
                self._detect_embedded_brand_matches(
                    collapsed_label_candidates=collapsed_label_candidates,
                    collapsed_primary_keyword_map=collapsed_primary_keyword_map,
                    official_labels=official_labels,
                    keyword_tokens=keyword_tokens,
                    display_name=brand.display_name,
                    registrable_domain=registrable_domain,
                )
            )
            matched_primary = sorted(set(matched_primary).union(embedded_primary))

            if (
                matched_primary
                or matched_secondary
                or matched_related
                or brand_stuffing_matches
            ):
                features.matched_brand_ids.append(brand.brand_id)

            features.matched_primary_keywords.extend(
                keyword
                for keyword in matched_primary
                if keyword not in features.matched_primary_keywords
            )
            features.matched_secondary_keywords.extend(
                keyword
                for keyword in matched_secondary
                if keyword not in features.matched_secondary_keywords
            )
            features.matched_related_keywords.extend(
                keyword
                for keyword in matched_related
                if keyword not in features.matched_related_keywords
            )
            features.brand_stuffing_matches.extend(
                match
                for match in brand_stuffing_matches
                if match not in features.brand_stuffing_matches
            )

            for official_domain in brand.official_domains:
                official_label_raw = extract_domain_label(
                    *extract_registrable_domain(official_domain, self._compound_tlds)
                )
                official_label = normalize_token(official_label_raw)
                for segment in raw_label_segments or [label.lower()]:
                    normalized_segment = normalize_token(segment)
                    is_leet_variant = (
                        segment != official_label_raw.lower()
                        and normalized_segment == official_label
                    )
                    if (
                        segment in raw_typo_variants
                        or normalized_segment in typo_variants
                        or looks_like_typosquatting(segment, official_label_raw)
                        or is_leet_variant
                    ):
                        message = f"{brand.display_name}:{registrable_domain}"
                        if message not in features.typosquatting_matches:
                            features.typosquatting_matches.append(message)
                            features.matched_brand_ids.append(brand.brand_id)
                        break

            for subdomain in subdomains:
                normalized_subdomain = normalize_token(subdomain)
                if normalized_subdomain in primary_keywords:
                    brand_tokens_in_subdomains.add(normalized_subdomain)
                    if brand.brand_id not in features.matched_brand_ids:
                        features.matched_brand_ids.append(brand.brand_id)

            if brand.brand_id in features.matched_brand_ids and tld not in brand.official_tlds:
                features.suspicious_tld = True
                if (
                    f"TLD {tld} no coincide con los TLD oficiales de {brand.display_name}."
                    not in features.evidence
                ):
                    features.evidence.append(
                        f"TLD {tld} no coincide con los TLD oficiales de {brand.display_name}."
                    )

        if features.typosquatting_matches:
            features.evidence.append(
                "Posible typosquatting frente a marcas del catalogo: "
                + ", ".join(features.typosquatting_matches)
                + "."
            )

        if features.brand_stuffing_matches:
            features.evidence.append(
                "Coincidencias de marca embebida en el dominio: "
                + ", ".join(features.brand_stuffing_matches)
                + "."
            )

        if (
            len(subdomains) >= self._deceptive_subdomain_threshold
            or brand_tokens_in_subdomains
        ) and not features.exact_brand_match:
            features.deceptive_subdomain = True
            features.suspicious_subdomain_tokens.extend(
                sorted(brand_tokens_in_subdomains)
            )
            descriptor = (
                ", ".join(sorted(brand_tokens_in_subdomains))
                if brand_tokens_in_subdomains
                else f"{len(subdomains)} subdominios"
            )
            features.evidence.append(
                f"Estructura de subdominios potencialmente enganosa: {descriptor}."
            )

        features.matched_brand_ids = sorted(set(features.matched_brand_ids))
        features.matched_official_domains = sorted(set(features.matched_official_domains))
        return features

    @staticmethod
    def _build_collapsed_keyword_map(
        keywords: tuple[str, ...],
    ) -> dict[str, str]:
        collapsed_keywords: dict[str, str] = {}
        for keyword in keywords:
            collapsed_keyword = collapse_text(keyword)
            if not collapsed_keyword:
                continue
            collapsed_keywords[collapsed_keyword] = normalize_token(keyword)
        return collapsed_keywords

    @staticmethod
    def _extract_keyword_tokens(brand) -> set[str]:
        return {
            token
            for value in (
                brand.display_name,
                *brand.primary_keywords,
                *brand.secondary_keywords,
                *brand.related_keywords,
            )
            for token in tokenize_text(value)
            if token
        }

    def _extract_official_labels(self, brand) -> set[str]:
        return {
            collapsed
            for collapsed in {
                collapse_text(
                    extract_domain_label(
                        *extract_registrable_domain(
                            official_domain, self._compound_tlds
                        )
                    )
                )
                for official_domain in brand.official_domains
            }
            if collapsed
        }

    @staticmethod
    def _detect_embedded_brand_matches(
        collapsed_label_candidates: set[str],
        collapsed_primary_keyword_map: dict[str, str],
        official_labels: set[str],
        keyword_tokens: set[str],
        display_name: str,
        registrable_domain: str,
    ) -> tuple[list[str], list[str]]:
        embedded_primary: set[str] = set()
        brand_stuffing_matches: set[str] = set()
        normalized_display_name = normalize_token(display_name)
        filtered_keyword_tokens = {
            token for token in keyword_tokens if token and len(token) >= 3
        }

        for candidate in collapsed_label_candidates:
            if not candidate or candidate in official_labels:
                continue

            normalized_keyword = collapsed_primary_keyword_map.get(candidate)
            if normalized_keyword and candidate not in official_labels:
                embedded_primary.add(normalized_keyword)
                brand_stuffing_matches.add(f"{display_name}:{registrable_domain}")
                continue

            for official_label in official_labels:
                if not official_label:
                    continue
                for token in filtered_keyword_tokens:
                    if token == official_label:
                        continue
                    if candidate in {
                        f"{official_label}{token}",
                        f"{token}{official_label}",
                    }:
                        embedded_primary.add(normalized_display_name)
                        brand_stuffing_matches.add(
                            f"{display_name}:{registrable_domain}"
                        )
                        break
                else:
                    continue
                break

        return sorted(embedded_primary), sorted(brand_stuffing_matches)
