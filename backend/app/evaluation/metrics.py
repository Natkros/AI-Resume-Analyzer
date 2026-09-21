"""Phase 43/44: standard IR/extraction metrics used to score the
deterministic pipeline against the gold dataset in data/evaluation/.
Kept dependency-free (no sklearn) since the sets involved are small.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PRF1:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


def precision_recall_f1(predicted: set[str], expected: set[str]) -> PRF1:
    tp = len(predicted & expected)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return PRF1(precision=precision, recall=recall, f1=f1, true_positives=tp, false_positives=fp, false_negatives=fn)


def average_prf1(results: list[PRF1]) -> PRF1:
    if not results:
        return PRF1(0.0, 0.0, 0.0, 0, 0, 0)
    n = len(results)
    return PRF1(
        precision=sum(r.precision for r in results) / n,
        recall=sum(r.recall for r in results) / n,
        f1=sum(r.f1 for r in results) / n,
        true_positives=sum(r.true_positives for r in results),
        false_positives=sum(r.false_positives for r in results),
        false_negatives=sum(r.false_negatives for r in results),
    )


def recall_at_k(retrieved_ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    top_k = set(retrieved_ranked[:k])
    return len(top_k & relevant) / len(relevant)


def mean_reciprocal_rank(retrieved_ranked: list[str], relevant: set[str]) -> float:
    for i, item in enumerate(retrieved_ranked, start=1):
        if item in relevant:
            return 1.0 / i
    return 0.0
