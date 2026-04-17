from __future__ import annotations

import re

from domain.models import BrandCatalog, DomainInput, FeatureSet
from domain.utils import (
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
                "Términos de ingeniería social detectados: "
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
            raw_typo_variants = {variant.lower() for variant in brand.typosquatting_variants}
            typo_variants = {
                normalize_token(variant) for variant in brand.typosquatting_variants
            }

            matched_primary = sorted(primary_keywords.intersection(url_tokens))
            matched_secondary = sorted(secondary_keywords.intersection(url_tokens))
            matched_related = sorted(related_keywords.intersection(url_tokens))

            if matched_primary or matched_secondary or matched_related:
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
                "Posible typosquatting frente a marcas del catálogo: "
                + ", ".join(features.typosquatting_matches)
                + "."
            )

        if (
            len(subdomains) >= self._deceptive_subdomain_threshold
            or brand_tokens_in_subdomains
        ) and not features.exact_brand_match:
            features.deceptive_subdomain = True
            features.suspicious_subdomain_tokens.extend(sorted(brand_tokens_in_subdomains))
            descriptor = (
                ", ".join(sorted(brand_tokens_in_subdomains))
                if brand_tokens_in_subdomains
                else f"{len(subdomains)} subdominios"
            )
            features.evidence.append(
                f"Estructura de subdominios potencialmente engañosa: {descriptor}."
            )

        features.matched_brand_ids = sorted(set(features.matched_brand_ids))
        features.matched_official_domains = sorted(set(features.matched_official_domains))
        return features
