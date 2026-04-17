"""
Prompt Evaluation Runner

Run this to evaluate how well your prompts perform:
    python -m tests.evaluation.eval_runner

This is NOT a pytest test — it's a standalone evaluation tool
that makes real LLM calls and scores the results.
"""

import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.prompt_service import PromptService
from app.core.config import settings


def load_test_cases() -> dict:
    cases_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
    with open(cases_path, "r") as f:
        return json.load(f)


def evaluate_response(response: str, test_case: dict) -> dict:
    """
    Score a single response against must_contain and must_not_contain rules.
    Returns a result dict with pass/fail and details.
    """
    response_lower = response.lower()
    failures = []

    # Check must_contain
    for term in test_case.get("must_contain", []):
        if term.lower() not in response_lower:
            failures.append(f"MISSING required term: '{term}'")

    # Check must_not_contain
    for term in test_case.get("must_not_contain", []):
        if term.lower() in response_lower:
            failures.append(f"CONTAINS forbidden term: '{term}'")

    passed = len(failures) == 0

    return {
        "test_id": test_case["id"],
        "category": test_case["category"],
        "description": test_case["description"],
        "input": test_case["input"],
        "response": response[:200] + "..." if len(response) > 200 else response,
        "passed": passed,
        "failures": failures
    }


def run_evaluation():
    """Run all test cases and print a report."""

    print("\n" + "="*60)
    print("PROMPT EVALUATION REPORT")
    print("="*60)

    data = load_test_cases()
    test_cases = data["test_cases"]

    # Import here to avoid issues during module load
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    prompt_service = PromptService()
    system_prompt = prompt_service.build_system_prompt()

    client = ChatCompletionsClient(
        endpoint=settings.github_model_endpoint,
        credential=AzureKeyCredential(settings.github_token)
    )

    results = []
    passed = 0
    failed = 0

    for tc in test_cases:
        print(f"\nRunning [{tc['id']}] {tc['description']}...")

        try:
            response = client.complete(
                messages=[
                    SystemMessage(system_prompt),
                    UserMessage(tc["input"])
                ],
                model=settings.github_model_name,
                temperature=0.3,   # Low temperature for eval consistency
                max_tokens=500
            )

            reply = response.choices[0].message.content
            result = evaluate_response(reply, tc)
            results.append(result)

            if result["passed"]:
                passed += 1
                print(f"  ✅ PASSED")
            else:
                failed += 1
                print(f"  ❌ FAILED")
                for failure in result["failures"]:
                    print(f"     → {failure}")

            # Small delay to avoid rate limits
            time.sleep(1)

        except Exception as e:
            print(f"  💥 ERROR: {str(e)}")
            failed += 1

    # Summary report
    total = passed + failed
    score = (passed / total * 100) if total > 0 else 0

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total tests : {total}")
    print(f"Passed      : {passed} ✅")
    print(f"Failed      : {failed} ❌")
    print(f"Score       : {score:.1f}%")

    # Category breakdown
    print("\nBY CATEGORY:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    for cat, counts in categories.items():
        cat_score = counts["passed"] / counts["total"] * 100
        print(f"  {cat:<20} {counts['passed']}/{counts['total']} ({cat_score:.0f}%)")

    print("="*60)

    # Save results to file
    output_path = "data/eval_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "score": score,
            "passed": passed,
            "failed": failed,
            "results": results
        }, f, indent=2)

    print(f"\nFull results saved to: {output_path}")
    return score


if __name__ == "__main__":
    run_evaluation()