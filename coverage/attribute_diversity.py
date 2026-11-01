"""Attribute Diversity coverage metric; importing this module never writes files."""
import csv
import math
from collections import Counter
from pathlib import Path

TASK_TYPES = ["information_lookup", "record_modification", "cancellation_or_refund",
              "new_creation", "troubleshooting", "verification_or_compliance",
              "policy_edge_case_or_refusal", "other"]
DOMAINS = {"tau2": ["airline", "retail", "telecom"],
           "synthetic": ["banking", "healthcare", "insurance", "manufacturing"]}


def normalized_entropy(counts, categories):
    unknown = set(counts) - set(categories)
    if unknown:
        raise ValueError(f"Unknown categories: {sorted(unknown)}")
    total = sum(counts[c] for c in categories)
    if total == 0 or len(categories) < 2:
        return 0.0
    probabilities = [counts[c] / total for c in categories if counts[c] > 0]
    return sum(-p * math.log(p) for p in probabilities) / math.log(len(categories))


def compute_attribute_diversity(labels_by_dataset):
    """Preserve the existing category definitions and observed tool vocabularies."""
    count_rows, score_rows = [], []
    for dataset, rows in labels_by_dataset.items():
        if not rows:
            raise ValueError(f"No labels for {dataset}")
        tool_counts = Counter(t for row in rows for t in set(row["tools"].split("|")) if t)
        attributes = {
            "domain": (Counter(r["domain"] for r in rows), DOMAINS[dataset]),
            "task_type": (Counter(r["task_type"] for r in rows), TASK_TYPES),
            "tools": (tool_counts, sorted(tool_counts)),
        }
        components = []
        for attribute, (counts, categories) in attributes.items():
            score = normalized_entropy(counts, categories)
            components.append(round(score, 4))
            score_rows.append(dict(dataset=dataset, attribute=attribute, score=round(score, 4)))
            count_rows.extend(dict(dataset=dataset, attribute=attribute, category=c, count=counts[c])
                              for c in categories)
        # Match the original implementation's rounding before averaging.
        score_rows.append(dict(dataset=dataset, attribute="average",
                               score=round(sum(components) / len(components), 4)))
    return count_rows, score_rows


def main():
    folder = Path(__file__).resolve().parent
    labels = {}
    for dataset in DOMAINS:
        with (folder / "labels" / f"labels_{dataset}.csv").open(newline="") as handle:
            labels[dataset] = list(csv.DictReader(handle))
    counts, scores = compute_attribute_diversity(labels)
    for filename, rows in [("attribute_counts.csv", counts), ("attribute_scores.csv", scores)]:
        with (folder / filename).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for row in scores:
        print(row)


if __name__ == "__main__":
    main()
