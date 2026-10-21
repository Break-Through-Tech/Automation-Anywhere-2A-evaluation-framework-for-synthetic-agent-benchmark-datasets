import math
from collections import Counter
from pathlib import Path
import pandas as pd
 
folder = Path(__file__).resolve().parent
 
TASK_TYPES = ["information_lookup", "record_modification", "cancellation_or_refund",
              "new_creation", "troubleshooting", "verification_or_compliance",
              "policy_edge_case_or_refusal", "other"]

DOMAINS = {"tau2": ["airline", "retail", "telecom"],
           "synthetic": ["banking", "healthcare", "insurance", "manufacturing"]}
 
 
def normalized_entropy(counts, categories):
    total = sum(counts[c] for c in categories)
    probabilities = [counts[c] / total for c in categories if counts[c] > 0]
    entropy = sum(-p * math.log(p) for p in probabilities)

    return entropy / math.log(len(categories))
 
 
count_rows, score_rows = [], []
for dataset in ["tau2", "synthetic"]:
    df = pd.read_csv(folder / "labels" / f"labels_{dataset}.csv")
 
    tool_counts = Counter(t for tools in df["tools"].fillna("") for t in set(tools.split("|")) if t)
 
    attributes = {
        "domain": (Counter(df["domain"]), DOMAINS[dataset]),
        "task_type": (Counter(df["task_type"]), TASK_TYPES),
        "tools": (tool_counts, sorted(tool_counts)),
    }
 
    for attribute, (counts, categories) in attributes.items():
        score = normalized_entropy(counts, categories)
        score_rows.append({"dataset": dataset, "attribute": attribute, "score": round(score, 4)})
        count_rows += [{"dataset": dataset, "attribute": attribute, "category": c, "count": counts[c]}
                       for c in categories]
 
    average = sum(r["score"] for r in score_rows[-3:]) / 3
    score_rows.append({"dataset": dataset, "attribute": "average", "score": round(average, 4)})
 
pd.DataFrame(count_rows).to_csv(folder / "attribute_counts.csv", index=False)
scores = pd.DataFrame(score_rows)
scores.to_csv(folder / "attribute_scores.csv", index=False)
print(scores.to_string(index=False))