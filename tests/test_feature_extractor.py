from __future__ import annotations


def test_extracts_typosquatting_and_social_features(
    input_handler, feature_extractor, brand_catalog_service
):
    input_data = input_handler.prepare("https://banc0lombia-verificacion.xyz/login")
    catalog = brand_catalog_service.get_catalog()

    features = feature_extractor.extract(input_data, catalog)

    assert features.tld == "xyz"
    assert features.suspicious_tld is True
    assert "verificacion" in features.social_engineering_terms
    assert "bancolombia" in features.matched_primary_keywords
    assert any("Bancolombia" in item for item in features.typosquatting_matches)


def test_extracts_exact_match_without_typosquatting(
    input_handler, feature_extractor, brand_catalog_service
):
    input_data = input_handler.prepare("https://www.bancolombia.com.co")
    catalog = brand_catalog_service.get_catalog()

    features = feature_extractor.extract(input_data, catalog)

    assert features.exact_brand_match is True
    assert not features.typosquatting_matches
    assert "bancolombia.com.co" in features.matched_official_domains


def test_detects_deceptive_subdomains(
    input_handler, feature_extractor, brand_catalog_service
):
    input_data = input_handler.prepare(
        "https://bancolombia.seguridad.example.com.co/login"
    )
    catalog = brand_catalog_service.get_catalog()

    features = feature_extractor.extract(input_data, catalog)

    assert features.deceptive_subdomain is True
    assert "bancolombia" in features.suspicious_subdomain_tokens


def test_detects_embedded_brand_keywords_in_registrable_domain(
    input_handler, feature_extractor, brand_catalog_service
):
    input_data = input_handler.prepare("https://hotelesdecameron.com")
    catalog = brand_catalog_service.get_catalog()

    features = feature_extractor.extract(input_data, catalog)

    assert "decameron" in features.matched_brand_ids
    assert "hoteles decameron" in features.matched_primary_keywords
    assert any("Decameron" in item for item in features.brand_stuffing_matches)
