from __future__ import annotations


def test_scoring_engine_breaks_down_matching_rules(
    input_handler,
    feature_extractor,
    brand_catalog_service,
    scoring_engine,
):
    input_data = input_handler.prepare("https://banc0lombia-verificacion.xyz/login")
    features = feature_extractor.extract(input_data, brand_catalog_service.get_catalog())

    score_result = scoring_engine.score(features)
    rule_ids = {rule.rule_id for rule in score_result.matched_rules}

    assert {"RN-04", "RN-05", "RN-07", "RN-10"} <= rule_ids
    assert score_result.total_score == sum(rule.weight for rule in score_result.matched_rules)


def test_scoring_engine_does_not_flag_exact_official_domain(
    input_handler,
    feature_extractor,
    brand_catalog_service,
    scoring_engine,
):
    input_data = input_handler.prepare("https://bancolombia.com.co")
    features = feature_extractor.extract(input_data, brand_catalog_service.get_catalog())

    score_result = scoring_engine.score(features)
    rule_ids = {rule.rule_id for rule in score_result.matched_rules}

    assert "RN-04" not in rule_ids
    assert "RN-05" not in rule_ids
