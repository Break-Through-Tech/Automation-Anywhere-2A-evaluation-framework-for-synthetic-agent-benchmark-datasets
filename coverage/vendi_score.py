"""
Coverage metric: normalized Vendi Score (VS/n) of task descriptions.

Embed each task description, build the n x n cosine similarity matrix K, and take
VS = exp(entropy of the eigenvalues of K/n). VS is the "effective number of distinct
tasks": 1 if all tasks are identical, n if all are orthogonal. VS/n puts it in [1/n, 1].

Note VS/n is not size-invariant (fewer tasks tend to score higher), so compare
groups of similar size or look at VS alongside it.

    python coverage/vendi_score.py      # writes coverage/vendi_scores.csv
"""

import csv
import sys
from pathlib import Path

import numpy as np

path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(path / "data"))

from loaders import load_tasks

output_path = path / "coverage" / "vendi_scores.csv"
MODEL_NAME = "all-MiniLM-L6-v2"


def embed(texts, model_name=MODEL_NAME):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name).encode(texts, normalize_embeddings=True)


def vendi_score(embeddings):
    x = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    k = x @ x.T  # cosine similarity matrix
    eigenvalues = np.linalg.eigvalsh(k / len(k))
    eigenvalues = eigenvalues[eigenvalues > 1e-12]  # 0 log 0 = 0; also drops float noise below 0
    return float(np.exp(-np.sum(eigenvalues * np.log(eigenvalues))))


if __name__ == "__main__":
    # self-check: identical vectors -> 1, orthogonal vectors -> n
    assert np.isclose(vendi_score(np.ones((5, 3))), 1)
    assert np.isclose(vendi_score(np.eye(4)), 4)

    tasks = load_tasks()
    embeddings = embed([t["description"] for t in tasks])

    groups = {}
    for i, t in enumerate(tasks):
        groups.setdefault((t["dataset"], "all"), []).append(i)
        groups.setdefault((t["dataset"], t["domain"]), []).append(i)

    rows = []
    for (dataset, domain), idx in groups.items():
        vs = vendi_score(embeddings[idx])
        rows.append({
            "dataset": dataset,
            "domain": domain,
            "n": len(idx),
            "vendi_score": round(vs, 4),
            "vendi_score_norm": round(vs / len(idx), 4),
        })

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["dataset", "domain", "n", "vendi_score", "vendi_score_norm"])
        writer.writeheader()
        writer.writerows(rows)

    for r in rows:
        print(f"{r['dataset']:10} {r['domain']:32} n={r['n']:4} VS={r['vendi_score']:8.3f} VS/n={r['vendi_score_norm']:.3f}")
    print(f"Wrote {len(rows)} rows to {output_path}")
