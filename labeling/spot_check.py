"""Spot-check the LLM labels.

Step 1 (make the sheet):   python scripts/spot_check.py make --labels outputs/labels_tau2.csv --n 30
Step 2: open outputs/spot_check_sheet.csv, read each task_text, fill in `task_type_ok`
        with y or n (and write the right label in `correct_task_type` when n).
Step 3 (score it):         python scripts/spot_check.py score
"""
import argparse
import pandas as pd

SHEET = "outputs/spot_check_sheet.csv"


def make(labels, n, seed):
    df = pd.read_csv(labels)
    # stratify: spread the sample across domains so one big domain can't hide errors
    by = "given_category" if "given_category" in df.columns else "domain"  # synthetic: 7 folders
    per = max(1, n // df[by].nunique())
    s = pd.concat([g.sample(min(per, len(g)), random_state=seed) for _, g in df.groupby(by)])
    if len(s) < n:
        s = pd.concat([s, df.drop(s.index).sample(n - len(s), random_state=seed)])
    s = s[["task_id", "domain"] + (["given_category"] if "given_category" in s.columns else []) + ["text", "tools", "task_type", "llm_rationale"]].rename(columns={"text": "task_text"})
    for c in ["task_type_ok", "correct_task_type", "notes"]:
        s[c] = ""
    s.to_csv(SHEET, index=False)
    print(f"wrote {SHEET} with {len(s)} rows")


def score():
    s = pd.read_csv(SHEET).fillna("")
    s = s[s["task_type_ok"].astype(str).str.strip() != ""]
    for col in ["task_type_ok"]:
        ok = (s[col].str.lower().str.strip() == "y").mean()
        print(f"{col}: {ok:.0%} correct over {len(s)} checked")
    bad = s[s["task_type_ok"].str.lower().str.strip() == "n"]
    if len(bad):
        print("\nWrong task_type labels (look for a pattern -> fix the prompt/classification, then relabel):")
        print(bad[["task_id", "task_type", "correct_task_type", "notes"]].to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "score"])
    ap.add_argument("--labels", default="outputs/labels_tau2.csv")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    make(a.labels, a.n, a.seed) if a.cmd == "make" else score()