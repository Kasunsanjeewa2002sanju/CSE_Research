"""
Plain-language grounded narrative generator for Stage 11 scenario results.

Guarantees:
- Every numerical figure, percentage, or index level cited is drawn strictly
  from the scenario output object.
- Transparently articulates the counterfactual difference (Scenario TRUE vs FALSE).
"""

from __future__ import annotations

from typing import Any, Dict


def generate_scenario_explanation(result: Dict[str, Any]) -> str:
    """
    Generate an econometric narrative grounded strictly in the output object figures.
    """
    headline = result["input"]["headline"]
    category = result["extraction"]["event_category"]
    stage = result["extraction"]["stage"]
    as_of = result["market_context"]["as_of_date"]
    aspi_curr = result["market_context"]["current_aspi_level"]
    is_stale = result["market_context"]["is_stale"]

    h1_true = result["scenarios"]["TRUE"]["horizons"]["1"]
    h1_false = result["scenarios"]["FALSE"]["horizons"]["1"]
    h1_impact = result["impact"]["horizons"]["1"]

    h5_true = result["scenarios"]["TRUE"]["horizons"]["5"]
    h5_false = result["scenarios"]["FALSE"]["horizons"]["5"]
    h5_impact = result["impact"]["horizons"]["5"]

    ev = result["historical_evidence"]

    stale_text = " (Note: date is beyond available database; ASPI level marked STALE)" if is_stale else ""

    lines = [
        f"**News Analysis:** \"{headline}\"",
        f"- **Category:** {category.replace('_', ' ').title()} | **Stage:** {stage.title()}",
        f"- **Market Baseline:** As of {as_of}, ASPI closed at {aspi_curr:,.2f}{stale_text}.",
        "",
        "**Forecast Comparison (Scenario TRUE vs FALSE):**",
        f"- **1-Day Horizon (h=1):**",
        f"  * Scenario TRUE (Event Occurs): Expected return is {h1_true['expected_log_return']*100:+.2f}% "
        f"(ASPI ~{h1_true['expected_aspi_level']:,.2f}), with calibrated P(Up) = {h1_true['prob_up']*100:.1f}%. "
        f"Conformal 80% range: [{h1_true['interval_80']['aspi_lower']:,.2f}, {h1_true['interval_80']['aspi_upper']:,.2f}].",
        f"  * Scenario FALSE (Status Quo): Expected return is {h1_false['expected_log_return']*100:+.2f}% "
        f"(ASPI ~{h1_false['expected_aspi_level']:,.2f}), with calibrated P(Up) = {h1_false['prob_up']*100:.1f}%.",
        f"  * **Net Event Impact:** {h1_impact['diff_log_return']*100:+.2f}% ({h1_impact['diff_aspi_level']:+.2f} ASPI points), "
        f"shifting directional probability by {h1_impact['diff_prob_up']*100:+.1f} percentage points.",
        "",
        f"- **5-Day Weekly Horizon (h=5):**",
        f"  * Scenario TRUE: Expected return is {h5_true['expected_log_return']*100:+.2f}% "
        f"(ASPI ~{h5_true['expected_aspi_level']:,.2f}), with calibrated P(Up) = {h5_true['prob_up']*100:.1f}%. "
        f"Conformal 80% range: [{h5_true['interval_80']['aspi_lower']:,.2f}, {h5_true['interval_80']['aspi_upper']:,.2f}].",
        f"  * Scenario FALSE: Expected return is {h5_false['expected_log_return']*100:+.2f}% "
        f"(ASPI ~{h5_false['expected_aspi_level']:,.2f}), with calibrated P(Up) = {h5_false['prob_up']*100:.1f}%.",
        f"  * **Net Event Impact:** {h5_impact['diff_log_return']*100:+.2f}% ({h5_impact['diff_aspi_level']:+.2f} ASPI points).",
        "",
        "**Historical Empirical Evidence (Stage 4 Event Study):**",
    ]

    if ev["has_historical_match"]:
        lines.extend([
            f"- Matching historical sample contains n={ev['n_events']} completed events ({ev['matching_type']} - {ev['matching_stage']}).",
            f"- Historical mean CAAR [0, +7 days] is {ev['mean_car']*100:+.2f}% (median: {ev['median_car']*100:+.2f}%), with Brown-Warner t-stat = {ev['t_statistic']:.2f} (p = {ev['t_pvalue']:.4f}).",
            f"- Evidence Strength Rating: **{ev['evidence_strength'].upper()}**" + (" (small sample warning applies: n < 5)" if ev['small_sample_warning'] else "") + ".",
        ])
    else:
        lines.append("- No direct electoral cycle match in Stage 4 database (evaluated under broad macroeconomic event dynamics; evidence strength: WEAK).")

    lines.extend([
        "",
        "> [!NOTE]",
        "> All figures are generated directly by the trained frozen model and walk-forward conformal residual calibration without hand-made price formulas.",
    ])

    return "\n".join(lines)
