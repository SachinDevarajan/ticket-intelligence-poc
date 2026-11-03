"""Run: python evaluation/run_evaluation.py (API must be running)."""
import json
import os
import sys
import time
from pathlib import Path
import httpx

BASE_URL = "http://127.0.0.1:8000/api/ai/tickets/analyze"
CASES = Path(__file__).with_name("test_cases.json")
LABELS = ["PAYMENT_ISSUE", "ACCOUNT_ISSUE", "PRODUCT_ISSUE", "DELIVERY_ISSUE", "GENERAL_FEEDBACK", "PRODUCT_ENQUIRY", "NEEDS_CLARIFICATION", "OTHER"]

# Groq's free tier allows only ~8000 tokens per minute, so calls are spaced out
# and rate-limited requests are retried. Override with EVAL_DELAY_SECONDS=0 on a paid tier.
DELAY_SECONDS = float(os.getenv("EVAL_DELAY_SECONDS", "8"))
MAX_ATTEMPTS = 6


def post_with_retry(client, payload, label):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = client.post(BASE_URL, json=payload)
        if response.status_code == 200:
            return response
        rate_limited = "429" in response.text or "rate_limit" in response.text.lower()
        if rate_limited and attempt < MAX_ATTEMPTS:
            wait = 15 * attempt
            print(f"{label}: rate limited, waiting {wait}s (attempt {attempt}/{MAX_ATTEMPTS})")
            time.sleep(wait)
            continue
        raise RuntimeError(f"{label} failed ({response.status_code}): {response.text}")


def macro_metrics(expected, predicted, labels):
    per_class = []
    for label in labels:
        tp = sum(e == label and p == label for e, p in zip(expected, predicted))
        fp = sum(e != label and p == label for e, p in zip(expected, predicted))
        fn = sum(e == label and p != label for e, p in zip(expected, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if sum(e == label for e in expected):
            per_class.append((precision, recall, f1))
    n = len(expected)
    return {
        "accuracy": sum(e == p for e, p in zip(expected, predicted)) / n if n else 0.0,
        "macro_precision": sum(x[0] for x in per_class) / len(per_class) if per_class else 0.0,
        "macro_recall": sum(x[1] for x in per_class) / len(per_class) if per_class else 0.0,
        "macro_f1": sum(x[2] for x in per_class) / len(per_class) if per_class else 0.0,
    }

def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    report = {"note": "Live model evaluation; results vary by model/provider. Category metrics use macro averaging over classes present in the expected labels.", "prompt_versions": {}}
    with httpx.Client(timeout=120) as client:
        for version in ("v1", "v2", "v3"):
            rows, expected, predicted = [], [], []
            for case in cases:
                print(f"Running {version} {case['id']} ...", flush=True)
                response = post_with_retry(client, {"query": case["query"], "prompt_version": version}, f"{version} {case['id']}")
                time.sleep(DELAY_SECONDS)
                output = response.json()
                expected.append(case["expected_category"])
                predicted.append(output["category"])
                rows.append({"id": case["id"], "expected_category": case["expected_category"], "predicted_category": output["category"], "expected_priority": case["expected_priority"], "predicted_priority": output["priority"], "expected_sentiment": case["expected_sentiment"], "predicted_sentiment": output["sentiment"], "ticket_id": output["ticket_id"]})
            report["prompt_versions"][version] = {"category_metrics": macro_metrics(expected, predicted, LABELS), "priority_accuracy": sum(r["expected_priority"] == r["predicted_priority"] for r in rows) / len(rows), "sentiment_accuracy": sum(r["expected_sentiment"] == r["predicted_sentiment"] for r in rows) / len(rows), "cases": rows}
    out = Path(__file__).with_name("evaluation_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved live evaluation report to {out}")
    for version, result in report["prompt_versions"].items():
        print(version, json.dumps(result["category_metrics"]), "priority_accuracy=", round(result["priority_accuracy"], 3))

if __name__ == "__main__":
    main()
