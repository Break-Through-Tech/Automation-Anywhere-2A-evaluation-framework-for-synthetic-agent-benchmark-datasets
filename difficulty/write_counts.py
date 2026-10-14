import csv
import sys
from pathlib import Path

path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(path / "data"))

from run_test_cases import load_test_case_classes

DOMAINS = [
    "banking_accounts_deposits",
    "banking_customer_onboarding",
    "banking_fraud_monitoring",
    "healthcare_patient_onboarding",
    "healthcare_prior_authorization",
    "insurance_claims_intake",
    "manufacturing_purchase_to_pay",
]

labels_path = path / "difficulty" / "synthetic_tool_labels.csv"
output_path = path / "difficulty" / "write_counts.csv"
END_TOOLS = {"SUCCESS", "FAILED", "CANCELLED", "HUMAN_IN_THE_LOOP"}


def load_labels():
    labels = {}

    with open(labels_path) as file:
        for row in csv.DictReader(file):
            labels[row["tool"]] = row["label"]

    return labels


def count_writes(test_case, labels):
    num_actions = 0
    num_write = 0
    unlabeled = []

    for tool_call in test_case.expected_tool_calls:
        name = tool_call["name"]
        if name in END_TOOLS:
            continue
        num_actions += 1
        if name not in labels:
            unlabeled.append(name)
        elif labels[name] == "write":
            num_write += 1
    return num_actions, num_write, unlabeled


if __name__ == "__main__":
    labels = load_labels()
    print(f"Loaded {len(labels)} tool labels")
    rows = []

    for domain in DOMAINS:
        classes = load_test_case_classes(domain)
        for test_cls in classes.values():
            test_case = test_cls()
            n_actions, n_write, unlabeled = count_writes(test_case, labels)

            if unlabeled:
                print(f"WARNING: {test_case.test_case_id} uses unlabeled tools: {unlabeled}")
            rows.append({
                "dataset": "synthetic",
                "domain": domain,
                "task_id": test_case.test_case_id,
                "num_actions": n_actions,
                "num_write": n_write,
            })

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["dataset", "domain", "task_id", "num_actions", "num_write"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")