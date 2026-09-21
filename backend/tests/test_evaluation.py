from app.evaluation.run_eval import evaluate_matching, evaluate_section_detection, evaluate_skill_extraction


def test_skill_extraction_meets_quality_bar():
    avg, details = evaluate_skill_extraction()
    assert details, "gold resume set should not be empty"
    assert avg.f1 >= 0.9, f"skill extraction F1 regressed: {avg.f1} ({details})"


def test_section_detection_meets_quality_bar():
    avg, details = evaluate_section_detection()
    assert details
    assert avg.f1 >= 0.9, f"section detection F1 regressed: {avg.f1} ({details})"


def test_skill_matching_meets_quality_bar():
    avg, details = evaluate_matching()
    assert details
    assert avg.f1 >= 0.9, f"skill matching F1 regressed: {avg.f1} ({details})"
