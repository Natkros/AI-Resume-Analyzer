"""Phase 44: evaluation harness. Runs the deterministic resume parser and
matching engine against the gold dataset in data/evaluation/ and reports
precision/recall/F1 for skill extraction, section detection, and skill
matching.

Usage:
    python -m app.evaluation.run_eval
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings
from app.evaluation.metrics import PRF1, average_prf1, precision_recall_f1
from app.pipelines.jd_parser import parse_job_description
from app.pipelines.resume_parser import parse_resume
from app.scoring.matching_engine import run_matching


def _gold_dir() -> Path:
    return get_settings().skills_data_dir.parent / "evaluation"


def evaluate_skill_extraction() -> tuple[PRF1, list[dict]]:
    gold_dir = _gold_dir() / "gold_resumes"
    per_resume: list[PRF1] = []
    details: list[dict] = []
    for path in sorted(gold_dir.glob("*.json")):
        gold = json.loads(path.read_text(encoding="utf-8"))
        parsed = parse_resume(gold["text"].encode("utf-8"), f"{gold['id']}.txt")
        result = precision_recall_f1(set(parsed.all_skills_flat), set(gold["expected_skills"]))
        per_resume.append(result)
        details.append({"id": gold["id"], "precision": result.precision, "recall": result.recall, "f1": result.f1})
    return average_prf1(per_resume), details


def evaluate_section_detection() -> tuple[PRF1, list[dict]]:
    gold_dir = _gold_dir() / "gold_resumes"
    per_resume: list[PRF1] = []
    details: list[dict] = []
    for path in sorted(gold_dir.glob("*.json")):
        gold = json.loads(path.read_text(encoding="utf-8"))
        parsed = parse_resume(gold["text"].encode("utf-8"), f"{gold['id']}.txt")
        result = precision_recall_f1(set(parsed.sections.keys()), set(gold["expected_sections"]))
        per_resume.append(result)
        details.append({"id": gold["id"], "precision": result.precision, "recall": result.recall, "f1": result.f1})
    return average_prf1(per_resume), details


def evaluate_matching() -> tuple[PRF1, list[dict]]:
    gold_path = _gold_dir() / "gold_jd_matches.json"
    gold_resumes_dir = _gold_dir() / "gold_resumes"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))

    resumes_by_id = {}
    for path in gold_resumes_dir.glob("*.json"):
        entry = json.loads(path.read_text(encoding="utf-8"))
        resumes_by_id[entry["id"]] = entry

    per_case: list[PRF1] = []
    details: list[dict] = []
    for case in gold["cases"]:
        resume_gold = resumes_by_id[case["resume_id"]]
        resume = parse_resume(resume_gold["text"].encode("utf-8"), f"{case['resume_id']}.txt")
        jd = parse_job_description(case["jd_text"])
        match = run_matching(resume, jd, embedder=None)

        predicted_matched = {m.skill for m in match.required_skill_matches}
        result = precision_recall_f1(predicted_matched, set(case["expected_matched_required"]))
        per_case.append(result)
        details.append({
            "resume_id": case["resume_id"], "precision": result.precision, "recall": result.recall, "f1": result.f1,
            "missing_matches_expected": case["expected_missing_required"],
            "missing_matches_actual": match.missing_required_skills,
        })
    return average_prf1(per_case), details


def run_all() -> dict:
    skill_avg, skill_details = evaluate_skill_extraction()
    section_avg, section_details = evaluate_section_detection()
    match_avg, match_details = evaluate_matching()
    return {
        "skill_extraction": {"average": vars(skill_avg), "per_resume": skill_details},
        "section_detection": {"average": vars(section_avg), "per_resume": section_details},
        "skill_matching": {"average": vars(match_avg), "per_case": match_details},
    }


if __name__ == "__main__":
    report = run_all()
    print(json.dumps(report, indent=2))
