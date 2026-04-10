from __future__ import annotations

from collections import Counter

from src.utils.schemas import RuleViolation, SimilarMatch, SuggestionResult


def _base_confidence_from_matches(matches: list[SimilarMatch]) -> float:
    if not matches:
        return 0.0
    return round(sum(m.similarity_score for m in matches) / len(matches), 3)


def _most_common_account(matches: list[SimilarMatch]) -> str | None:
    if not matches:
        return None
    counts = Counter(match.account_code for match in matches)
    return counts.most_common(1)[0][0]


def build_suggestion(
    matches: list[SimilarMatch],
    rule_violations: list[RuleViolation],
    fallback_cost_center: str | None = None,
    fallback_project_code: str | None = None,
) -> SuggestionResult:
    blocking = any(v.severity == "blocking" for v in rule_violations)

    suggested_account = _most_common_account(matches)
    confidence = _base_confidence_from_matches(matches)

    reasons: list[str] = []

    if blocking:
        reasons.append("Blocking rule violation detected.")
        decision = "stop"
        confidence = 0.0
    else:
        if matches:
            reasons.append("Suggestion based on similar historical records.")
        else:
            reasons.append("No sufficiently similar historical records found.")

        if rule_violations:
            reasons.append("One or more warning-level rules were triggered.")
            confidence = max(confidence - 0.15, 0.0)

        if confidence >= 0.75 and suggested_account is not None:
            decision = "suggest"
            reasons.append("Confidence is high enough for a suggestion.")
        else:
            decision = "review"
            reasons.append("Confidence is not high enough for automatic suggestion routing.")

    return SuggestionResult(
        suggested_account=suggested_account,
        suggested_cost_center=fallback_cost_center,
        suggested_project_code=fallback_project_code,
        confidence=confidence,
        decision=decision,
        reasons=reasons,
        rule_violations=rule_violations,
        similar_matches=matches,
    )
