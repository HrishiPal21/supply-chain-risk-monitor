"""
Smoke test — runs one end-to-end pipeline query and asserts all critical fields
are present and sane. No mocking; hits real APIs.

Usage:
    python3 smoke_test.py
"""

import sys
import os
import logging

# Must be set before importing agents so config.py loads .env
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s %(levelname)s: %(message)s",
)
for ns in ("agents", "tools"):
    logging.getLogger(ns).setLevel(logging.INFO)

from agents.graph import run_pipeline  # noqa: E402 — path must be set first

QUERY   = "semiconductor supply chain disruption from Taiwan geopolitical risk"
COMPANY = ""   # no ticker → industry-level exposure
REGION  = "Taiwan"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  {PASS}  {label}")
    else:
        tag = f" ({detail})" if detail else ""
        print(f"  {FAIL}  {label}{tag}")
        failures.append(label)


def main() -> None:
    print(f"\nRunning pipeline: {QUERY!r}\n{'─' * 60}")
    try:
        result = run_pipeline(query=QUERY, company=COMPANY, region=REGION)
    except Exception as exc:
        print(f"  {FAIL}  Pipeline raised an exception: {exc}")
        sys.exit(1)

    print(f"\n{'─' * 60}\nChecking state fields:\n")

    # ── Data retrieval ────────────────────────────────────────────────────────
    docs = result.get("retrieved_docs", [])
    check("retrieved_docs is a list",     isinstance(docs, list))
    check("at least 1 doc retrieved",     len(docs) >= 1,         f"got {len(docs)}")
    check("partial_context is bool",      isinstance(result.get("partial_context"), bool))

    usable = [d for d in docs if (d.get("text") or "").strip()]
    check("at least 1 doc has text",      len(usable) >= 1,       f"usable={len(usable)}/{len(docs)}")

    # ── Exposure assessment ───────────────────────────────────────────────────
    level = result.get("exposure_level")
    check("exposure_level present",       level is not None)
    check("exposure_level valid value",   level in {"Critical","High","Moderate","Low","Minimal","Unknown"},
          f"got {level!r}")

    mult = result.get("exposure_multiplier")
    check("exposure_multiplier present",  mult is not None)
    check("exposure_multiplier 0–1",      mult is not None and 0.0 <= mult <= 1.0,  f"got {mult}")

    check("exposure_summary present",     bool(result.get("exposure_summary")))

    # ── Analyst outputs ───────────────────────────────────────────────────────
    check("bear_analysis present",        bool(result.get("bear_analysis")))
    check("bull_analysis present",        bool(result.get("bull_analysis")))
    check("geopolitical_analysis present", bool(result.get("geopolitical_analysis")))

    # ── Judge ─────────────────────────────────────────────────────────────────
    raw   = result.get("raw_risk_score")
    adj   = result.get("risk_score")
    check("raw_risk_score present",       raw is not None)
    check("raw_risk_score 0–100",         raw is not None and 0 <= raw <= 100,  f"got {raw}")
    check("risk_score present",           adj is not None)
    check("risk_score 0–100",             adj is not None and 0 <= adj <= 100,  f"got {adj}")

    fo = result.get("final_output") or {}
    check("final_output is dict",         isinstance(fo, dict))
    for key in ("verdict", "risk_label", "recommended_action",
                "top_3_risks", "top_3_mitigants", "consensus_points"):
        check(f"final_output.{key} present", key in fo and fo[key] not in (None, "", []))

    # ── GuardRail ─────────────────────────────────────────────────────────────
    gr = result.get("guardrail_report") or {}
    check("guardrail_report is dict",     isinstance(gr, dict))
    check("guardrail trust_scores present", "trust_scores" in gr)
    check("guardrail overall_confidence present",
          gr.get("overall_confidence") in {"Low", "Medium", "High"},
          f"got {gr.get('overall_confidence')!r}")
    check("guardrail confidence_band present",
          isinstance(gr.get("confidence_band"), dict))

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"Score: {adj}/100  |  Exposure: {level}  |  Multiplier: {mult}")
    print(f"Label: {fo.get('risk_label')}  |  Action: {fo.get('recommended_action')}")
    print(f"GuardRail confidence: {gr.get('overall_confidence')}")
    print(f"Failed sources: {result.get('failed_sources') or 'none'}")
    print(f"{'─' * 60}\n")

    if failures:
        print(f"{FAIL}  {len(failures)} check(s) failed: {', '.join(failures)}\n")
        sys.exit(1)
    else:
        print(f"{PASS}  All checks passed.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
