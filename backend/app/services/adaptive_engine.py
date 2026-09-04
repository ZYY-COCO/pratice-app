"""Pure, deterministic primitives for adaptive practice V1.

This module deliberately has no FastAPI or Supabase dependency.  Recommendation
decisions and model updates can therefore be replayed from the audit log and
unit-tested without application infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import math
import random
from typing import Iterable, Sequence


STRATEGY_VERSION = "adaptive-delivery-v1"
MODEL_VERSION = "theta-shrinkage-v1"

DIFFICULTY_THETA = {
    1: -1.6,
    2: -0.8,
    3: 0.0,
    4: 0.8,
    5: 1.6,
}

EXAM_SUBJECTS = {
    "Z001": frozenset({"中华文化", "英语运用", "逻辑推理"}),
    "Z002": frozenset({"中华文化", "英语运用", "数学基础"}),
}


class _StringEnum(str, Enum):
    """String-valued enum with ``StrEnum`` semantics on Python 3.10+."""

    def __str__(self) -> str:
        return self.value


class DiagnosticStatus(_StringEnum):
    NEW = "NEW"
    PROBING = "PROBING"
    VERIFYING = "VERIFYING"
    CALIBRATING = "CALIBRATING"
    STABLE = "STABLE"
    RECALIBRATING = "RECALIBRATING"


class TargetZone(_StringEnum):
    DIAGNOSTIC = "diagnostic"
    VERIFY = "verify"
    CONSOLIDATION = "consolidation"
    MAIN = "main"
    CHALLENGE = "challenge"
    COVERAGE = "coverage"


@dataclass(frozen=True, slots=True)
class AbilityState:
    theta: float = 0.0
    uncertainty: float = 1.6
    effective_evidence: float = 0.0
    reliable_first_attempt_count: int = 0
    diagnostic_status: DiagnosticStatus = DiagnosticStatus.NEW
    pending_conflict_count: int = 0
    state_version: int = 0


@dataclass(frozen=True, slots=True)
class EvidenceContext:
    is_first_attempt: bool = True
    answer_seen: bool = False
    question_valid: bool = True
    quality_weight: float = 1.0
    used_time: int | None = None
    estimated_time: int | None = None


@dataclass(frozen=True, slots=True)
class EvidenceResult:
    weight: float
    reliable_first_attempt: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Observation:
    question_id: str
    difficulty: int
    is_correct: bool
    module: str
    submodule: str
    question_type: str = "single_choice"
    evidence_weight: float = 1.0
    is_first_attempt: bool = True
    position: int = 0

    @property
    def skill_key(self) -> tuple[str, str, str]:
        return (self.module, self.submodule, self.question_type)


@dataclass(frozen=True, slots=True)
class Inversion:
    low_question_id: str
    high_question_id: str
    skill_key: tuple[str, str, str]
    difficulty_gap: int


@dataclass(frozen=True, slots=True)
class TargetPlan:
    difficulty: int
    zone: TargetZone
    reason_codes: tuple[str, ...]
    is_diagnostic: bool = False
    is_challenge: bool = False


@dataclass(frozen=True, slots=True)
class Candidate:
    question_id: str
    difficulty: int
    module: str
    submodule: str
    question_type: str = "single_choice"
    quality_weight: float = 0.7
    is_diagnostic_candidate: bool = False
    diagnostic_priority: float = 0.0
    empirical_difficulty: float | None = None
    topic_theta: float | None = None
    topic_evidence: float = 0.0
    weak_topic_value: float = 0.0
    due_review_value: float = 0.0
    coverage_value: float = 0.5
    exploration_value: float = 0.5
    recent_exposure_penalty: float = 0.0
    same_topic_penalty: float = 0.0
    same_type_penalty: float = 0.0


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    candidate: Candidate
    score: float
    predicted_probability: float
    score_components: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModelUpdate:
    predicted_probability: float
    evidence_weight: float
    delta_theta: float
    subject_before: AbilityState
    subject_after: AbilityState
    topic_before: AbilityState
    topic_after: AbilityState
    inversion_pending: bool = False


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def validate_scope(exam_code: str, subject: str) -> tuple[str, str]:
    """Validate the non-negotiable user + exam + subject isolation boundary."""

    normalized_exam = str(exam_code or "").strip().upper()
    normalized_subject = str(subject or "").strip()
    if normalized_exam not in EXAM_SUBJECTS:
        raise ValueError("exam_code must be Z001 or Z002")
    if normalized_subject not in EXAM_SUBJECTS[normalized_exam]:
        raise ValueError(f"subject {normalized_subject!r} does not belong to {normalized_exam}")
    return normalized_exam, normalized_subject


def difficulty_to_theta(difficulty: int) -> float:
    try:
        return DIFFICULTY_THETA[int(difficulty)]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("difficulty must be between 1 and 5") from exc


def sigmoid(value: float) -> float:
    if value >= 0:
        exponent = math.exp(-value)
        return 1.0 / (1.0 + exponent)
    exponent = math.exp(value)
    return exponent / (1.0 + exponent)


def predict_correct_probability(
    theta: float,
    *,
    difficulty: int | None = None,
    item_b: float | None = None,
    guessing: float = 0.25,
    slip: float = 0.05,
    discrimination: float = 1.3,
) -> float:
    """Return a bounded four-choice response probability.

    ``item_b`` is used for empirically calibrated items; otherwise the initial
    D1-D5 map is used.  V1 keeps guessing and slip explicit instead of claiming
    that manually assigned difficulty is already an IRT parameter.
    """

    if item_b is None:
        if difficulty is None:
            raise ValueError("difficulty or item_b is required")
        item_b = difficulty_to_theta(difficulty)
    guessing = clamp(guessing, 0.0, 0.95)
    slip = clamp(slip, 0.0, 0.95)
    if guessing + slip >= 1.0:
        raise ValueError("guessing + slip must be below 1")
    probability = guessing + (1.0 - guessing - slip) * sigmoid(
        discrimination * (float(theta) - float(item_b))
    )
    return clamp(probability, guessing, 1.0 - slip)


def shrink_topic_theta(subject_theta: float, topic_theta: float, topic_evidence: float) -> tuple[float, float]:
    """Shrink sparse topic estimates toward the isolated subject estimate."""

    evidence = max(0.0, float(topic_evidence))
    shrinkage = evidence / (evidence + 8.0)
    effective = shrinkage * float(topic_theta) + (1.0 - shrinkage) * float(subject_theta)
    return effective, shrinkage


def compute_evidence_weight(context: EvidenceContext) -> EvidenceResult:
    """Turn answer provenance into a conservative, auditable evidence weight."""

    reasons: list[str] = []
    if context.answer_seen:
        return EvidenceResult(0.0, False, ("answer_seen",))
    if not context.question_valid:
        return EvidenceResult(0.0, False, ("invalid_question",))

    weight = 1.0 if context.is_first_attempt else 0.25
    reasons.append("first_attempt" if context.is_first_attempt else "repeat_attempt")

    quality = clamp(context.quality_weight, 0.0, 1.0)
    weight *= quality
    if quality < 0.999:
        reasons.append("question_quality_adjusted")

    if context.used_time is not None and context.estimated_time:
        ratio = max(0.0, float(context.used_time)) / max(1.0, float(context.estimated_time))
        if ratio < 0.15 or ratio > 5.0:
            weight *= 0.5
            reasons.append("extreme_duration")

    weight = clamp(weight, 0.0, 1.0)
    reliable = context.is_first_attempt and weight >= 0.7
    return EvidenceResult(round(weight, 6), reliable, tuple(reasons))


def detect_inversion(
    observations: Sequence[Observation],
    *,
    minimum_weight: float = 0.7,
) -> Inversion | None:
    """Detect a reliable low-wrong/high-correct pair for the same skill form."""

    ordered = sorted(observations, key=lambda item: (item.position, item.question_id))
    for high in reversed(ordered):
        if (
            not high.is_correct
            or not high.is_first_attempt
            or high.evidence_weight < minimum_weight
        ):
            continue
        for low in reversed(ordered):
            if low.question_id == high.question_id:
                continue
            if (
                low.is_correct
                or not low.is_first_attempt
                or low.evidence_weight < minimum_weight
                or low.skill_key != high.skill_key
            ):
                continue
            gap = int(high.difficulty) - int(low.difficulty)
            if gap >= 2:
                return Inversion(
                    low_question_id=low.question_id,
                    high_question_id=high.question_id,
                    skill_key=high.skill_key,
                    difficulty_gap=gap,
                )
    return None


def _next_status(
    before: AbilityState,
    *,
    evidence_after: float,
    reliable_count_after: int,
    uncertainty_after: float,
    pending_conflict_count: int,
    coverage_ready: bool = True,
) -> DiagnosticStatus:
    if pending_conflict_count > 0:
        return (
            DiagnosticStatus.RECALIBRATING
            if before.diagnostic_status in {
                DiagnosticStatus.STABLE,
                DiagnosticStatus.RECALIBRATING,
            }
            else DiagnosticStatus.VERIFYING
        )
    if reliable_count_after < 4:
        return DiagnosticStatus.PROBING
    if (
        reliable_count_after >= 20
        and evidence_after >= 18.0
        and uncertainty_after <= 0.75
        and coverage_ready
    ):
        return DiagnosticStatus.STABLE
    return DiagnosticStatus.CALIBRATING


def _updated_uncertainty(current: float, evidence_weight: float) -> float:
    return round(max(0.25, float(current) * math.exp(-0.045 * max(0.0, evidence_weight))), 6)


def update_ability(
    subject_state: AbilityState,
    topic_state: AbilityState,
    *,
    difficulty: int,
    is_correct: bool,
    evidence: EvidenceResult,
    empirical_difficulty: float | None = None,
    inversion_pending: bool = False,
    conflict_resolved: bool = False,
    subject_coverage_ready: bool = True,
) -> ModelUpdate:
    """Apply one bounded V1 update to subject and topic state.

    An inversion lowers conclusion confidence by setting a verification state;
    it does not erase otherwise reliable raw answer evidence.
    """

    effective_theta, _ = shrink_topic_theta(
        subject_state.theta,
        topic_state.theta,
        topic_state.effective_evidence,
    )
    probability = predict_correct_probability(
        effective_theta,
        difficulty=difficulty,
        item_b=empirical_difficulty,
    )
    weight = evidence.weight
    actual = 1.0 if is_correct else 0.0
    learning_rate = 0.08 + 0.22 * math.exp(-subject_state.effective_evidence / 12.0)
    delta = clamp(learning_rate * weight * (actual - probability), -0.25, 0.25)

    reliable_increment = 1 if evidence.reliable_first_attempt else 0
    pending_count = max(
        0,
        subject_state.pending_conflict_count
        + (1 if inversion_pending else 0)
        - (1 if conflict_resolved else 0),
    )
    subject_evidence = subject_state.effective_evidence + weight
    subject_reliable = subject_state.reliable_first_attempt_count + reliable_increment
    subject_uncertainty = _updated_uncertainty(subject_state.uncertainty, weight)
    if inversion_pending:
        subject_uncertainty = round(min(2.5, max(subject_uncertainty, subject_state.uncertainty * 1.12)), 6)
    subject_after = AbilityState(
        theta=round(clamp(subject_state.theta + delta, -3.0, 3.0), 6),
        uncertainty=subject_uncertainty,
        effective_evidence=round(subject_evidence, 6),
        reliable_first_attempt_count=subject_reliable,
        diagnostic_status=_next_status(
            subject_state,
            evidence_after=subject_evidence,
            reliable_count_after=subject_reliable,
            uncertainty_after=subject_uncertainty,
            pending_conflict_count=pending_count,
            coverage_ready=subject_coverage_ready,
        ),
        pending_conflict_count=pending_count,
        state_version=subject_state.state_version + 1,
    )

    topic_rate = 0.08 + 0.22 * math.exp(-topic_state.effective_evidence / 12.0)
    topic_probability = predict_correct_probability(
        topic_state.theta,
        difficulty=difficulty,
        item_b=empirical_difficulty,
    )
    topic_delta = clamp(topic_rate * weight * (actual - topic_probability), -0.25, 0.25)
    topic_evidence = topic_state.effective_evidence + weight
    topic_reliable = topic_state.reliable_first_attempt_count + reliable_increment
    topic_pending = max(
        0,
        topic_state.pending_conflict_count
        + (1 if inversion_pending else 0)
        - (1 if conflict_resolved else 0),
    )
    topic_uncertainty = _updated_uncertainty(topic_state.uncertainty, weight)
    if inversion_pending:
        topic_uncertainty = round(min(2.5, max(topic_uncertainty, topic_state.uncertainty * 1.12)), 6)
    topic_after = AbilityState(
        theta=round(clamp(topic_state.theta + topic_delta, -3.0, 3.0), 6),
        uncertainty=topic_uncertainty,
        effective_evidence=round(topic_evidence, 6),
        reliable_first_attempt_count=topic_reliable,
        diagnostic_status=_next_status(
            topic_state,
            evidence_after=topic_evidence,
            reliable_count_after=topic_reliable,
            uncertainty_after=topic_uncertainty,
            pending_conflict_count=topic_pending,
        ),
        pending_conflict_count=topic_pending,
        state_version=topic_state.state_version + 1,
    )

    return ModelUpdate(
        predicted_probability=round(probability, 6),
        evidence_weight=weight,
        delta_theta=round(delta, 6),
        subject_before=subject_state,
        subject_after=subject_after,
        topic_before=topic_state,
        topic_after=topic_after,
        inversion_pending=inversion_pending,
    )


def can_unlock_d5(
    observations: Sequence[Observation],
    *,
    preference: str = "standard",
    pending_conflicts: int = 0,
    accepted_challenge: bool = False,
) -> bool:
    if pending_conflicts > 0 or (preference != "challenge" and not accepted_challenge):
        return False
    reliable_correct = [
        item
        for item in observations
        if item.is_correct and item.is_first_attempt and item.evidence_weight >= 0.7
    ]
    has_d3 = any(item.difficulty == 3 for item in reliable_correct)
    # The V1 gate intentionally requires two distinct D4 confirmations.  A D5
    # answer is a challenge signal, not a substitute for either D4 anchor.
    d4_question_ids = {item.question_id for item in reliable_correct if item.difficulty == 4}
    return has_d3 and len(d4_question_ids) >= 2


def _consecutive_count(observations: Sequence[Observation], expected: bool) -> int:
    count = 0
    for item in reversed(observations):
        if item.is_correct is not expected:
            break
        count += 1
    return count


def theta_to_difficulty(theta: float) -> int:
    return min(DIFFICULTY_THETA, key=lambda difficulty: abs(DIFFICULTY_THETA[difficulty] - theta))


def plan_next_target(
    *,
    position: int,
    subject_state: AbilityState,
    observations: Sequence[Observation],
    question_count: int = 8,
    preference: str = "standard",
    accepted_challenge: bool = False,
    previous_was_challenge: bool = False,
    pending_verification_count: int = 0,
    previous_was_verification: bool = False,
    pending_verification: bool | None = None,
) -> TargetPlan:
    """Plan one question, including the fixed eight-question cold-start flow."""

    if position < 1:
        raise ValueError("position must be positive")
    if question_count < 1:
        raise ValueError("question_count must be positive")
    previous = list(observations)
    wrong_streak = _consecutive_count(previous, False)
    correct_streak = _consecutive_count(previous, True)
    inversion = detect_inversion(previous)
    detected_pending = subject_state.pending_conflict_count > 0 or inversion is not None
    # Persistence orchestration can explicitly pause verification when the
    # conflict is already terminal, outside the selected specialty scope, or
    # temporarily lacks a trustworthy parallel item.  Keeping ``None`` as the
    # default preserves this pure helper's standalone inversion detection.
    pending = detected_pending if pending_verification is None else bool(pending_verification)

    cold_start = subject_state.diagnostic_status in {
        DiagnosticStatus.NEW,
        DiagnosticStatus.PROBING,
        DiagnosticStatus.VERIFYING,
    } or subject_state.reliable_first_attempt_count < 8

    if position == question_count:
        # Closing protection is a session-level invariant: the final slot must
        # not be consumed by a verification or challenge branch.  Selecting a
        # confidence-building item here does not resolve a pending inversion;
        # the immutable ability state carries it into the learner's next run.
        closing_base = min(4, theta_to_difficulty(subject_state.theta))
        return TargetPlan(
            max(1, closing_base - 1),
            TargetZone.CONSOLIDATION,
            ("positive_finish",),
        )

    if pending:
        if previous_was_verification:
            recovery = int(clamp(theta_to_difficulty(subject_state.theta), 1, 4))
            return TargetPlan(
                recovery,
                TargetZone.COVERAGE,
                ("verification_interleave",),
                False,
            )
        target = 2 if max(0, int(pending_verification_count)) % 2 == 0 else 3
        return TargetPlan(target, TargetZone.VERIFY, ("inversion_parallel_recheck",), True)

    if cold_start and position <= 8:
        if position == 1:
            return TargetPlan(2, TargetZone.DIAGNOSTIC, ("cold_start_d2_doorway",), True)
        if position == 2:
            first_correct = bool(previous and previous[0].is_correct)
            return TargetPlan(
                3 if first_correct else 1,
                TargetZone.DIAGNOSTIC,
                ("probe_upper_bound" if first_correct else "protect_early_experience",),
                True,
            )
        if wrong_streak >= 2:
            last_difficulty = previous[-1].difficulty if previous else 2
            return TargetPlan(
                max(1, last_difficulty - 1),
                TargetZone.CONSOLIDATION,
                ("two_wrong_protection",),
                position <= 4,
            )
        if previous_was_challenge:
            last_difficulty = previous[-1].difficulty if previous else 2
            return TargetPlan(
                max(1, last_difficulty - 1),
                TargetZone.DIAGNOSTIC if position <= 4 else TargetZone.CONSOLIDATION,
                ("challenge_recovery",),
                position <= 4,
            )
        if position <= 4:
            if len(previous) >= 2 and all(item.is_correct for item in previous[-2:]):
                return TargetPlan(
                    min(4, previous[-1].difficulty + 1),
                    TargetZone.DIAGNOSTIC,
                    ("probe_upper_bound",),
                    True,
                    True,
                )
            last_difficulty = previous[-1].difficulty if previous else 2
            # A learner can skip every item shown so far.  In that case there
            # is no answer evidence to branch on, so keep the neutral D2 probe
            # instead of indexing an empty observation list.
            target = (
                last_difficulty
                if not previous or previous[-1].is_correct
                else max(1, last_difficulty - 1)
            )
            return TargetPlan(target, TargetZone.DIAGNOSTIC, ("confirm_initial_boundary",), True)

        base = clamp(theta_to_difficulty(subject_state.theta), 1, 4)
        # Once the initial boundary is usable, spend remaining warm-up slots on
        # uncovered D1-D4 levels instead of mechanically repeating the current
        # bucket. Severe frustration protection still wins over a D4 showcase.
        seen_levels = {item.difficulty for item in previous if 1 <= item.difficulty <= 4}
        missing_levels = [level for level in range(1, 5) if level not in seen_levels]
        if missing_levels and position <= 7:
            eligible_missing = list(missing_levels)
            if wrong_streak >= 3:
                eligible_missing = [level for level in eligible_missing if level <= int(base)]
            if eligible_missing:
                target_missing = min(
                    eligible_missing,
                    key=lambda level: (abs(level - int(base)), level),
                )
                return TargetPlan(
                    target_missing,
                    TargetZone.COVERAGE if target_missing <= int(base) else TargetZone.CHALLENGE,
                    ("complete_warmup_difficulty_coverage",),
                    False,
                    target_missing > int(base),
                )

        if position == 6:
            return TargetPlan(int(base), TargetZone.COVERAGE, ("broaden_topic_coverage",))
        if position == 7 and wrong_streak == 0 and preference != "steady":
            challenge_difficulty = min(4, int(base) + 1)
            if can_unlock_d5(
                previous,
                preference=preference,
                pending_conflicts=subject_state.pending_conflict_count,
                accepted_challenge=accepted_challenge,
            ):
                challenge_difficulty = 5
            return TargetPlan(challenge_difficulty, TargetZone.CHALLENGE, ("bounded_challenge",), False, True)
        return TargetPlan(int(base), TargetZone.MAIN, ("early_matched_training",))

    # D5 is always a bounded challenge in V1.  Even a very high theta must not
    # turn ordinary matched-training slots into an unlimited stream of D5s;
    # the explicit anchor gate below owns every D5 exposure.
    base = min(4, theta_to_difficulty(subject_state.theta))
    if wrong_streak >= 2:
        return TargetPlan(max(1, base - 1), TargetZone.CONSOLIDATION, ("two_wrong_protection",))
    if previous_was_challenge:
        last_difficulty = previous[-1].difficulty if previous else base + 1
        target = max(1, min(base, last_difficulty - 1))
        return TargetPlan(target, TargetZone.CONSOLIDATION, ("challenge_recovery",))
    if correct_streak >= 3:
        challenge = min(5, base + 1)
        if challenge == 5 and not can_unlock_d5(
            previous,
            preference=preference,
            pending_conflicts=subject_state.pending_conflict_count,
            accepted_challenge=accepted_challenge,
        ):
            challenge = 4
        return TargetPlan(challenge, TargetZone.CHALLENGE, ("three_correct_challenge",), False, True)

    cycle = (position - 1) % 10
    consolidation_slots = {0, 8, 9} if preference == "steady" else {0, 9}
    challenge_slots = (
        {7}
        if preference == "steady"
        else ({2, 4, 7} if preference == "challenge" else {4, 7})
    )
    if cycle in consolidation_slots:
        return TargetPlan(max(1, base - 1), TargetZone.CONSOLIDATION, ("round_consolidation",))
    if cycle in challenge_slots:
        challenge = min(5, base + 1)
        if challenge == 5 and not can_unlock_d5(
            previous,
            preference=preference,
            pending_conflicts=subject_state.pending_conflict_count,
            accepted_challenge=accepted_challenge,
        ):
            challenge = 4
        return TargetPlan(challenge, TargetZone.CHALLENGE, ("scheduled_challenge",), False, True)
    return TargetPlan(base, TargetZone.MAIN, ("matched_training",))


def plan_comprehensive_targets(
    *,
    subject_state: AbilityState,
    question_count: int,
    preference: str = "standard",
    accepted_challenge: bool = False,
) -> tuple[TargetPlan, ...]:
    """Build an immutable round blueprint without using answers from the round.

    Comprehensive practice reveals feedback only after the learner submits the
    whole round.  Its questions must therefore be selected from one pre-round
    ability snapshot instead of pretending that answers are available between
    positions.  The fixed blueprint still gives a new learner D1-D4 coverage
    and gives an established learner the same consolidation/main/challenge
    shape as the sequential policy.
    """

    if question_count < 1:
        raise ValueError("question_count must be positive")
    if preference not in {"steady", "standard", "challenge"}:
        raise ValueError("unsupported preference")

    cold_start = subject_state.diagnostic_status in {
        DiagnosticStatus.NEW,
        DiagnosticStatus.PROBING,
        DiagnosticStatus.VERIFYING,
    } or subject_state.reliable_first_attempt_count < 8
    base = int(clamp(theta_to_difficulty(subject_state.theta), 1, 4))
    plans: list[TargetPlan] = []

    if cold_start:
        doorway = (2, 3, 1, 4)
        for position in range(1, question_count + 1):
            if position <= len(doorway):
                difficulty = doorway[position - 1]
                plans.append(
                    TargetPlan(
                        difficulty,
                        TargetZone.DIAGNOSTIC,
                        ("comprehensive_cold_start_coverage",),
                        True,
                        difficulty >= 4,
                    )
                )
                continue
            if position == question_count:
                plans.append(
                    TargetPlan(
                        max(1, base - 1),
                        TargetZone.CONSOLIDATION,
                        ("positive_finish",),
                    )
                )
                continue
            cycle = (position - 5) % 3
            if cycle == 0:
                plans.append(
                    TargetPlan(base, TargetZone.MAIN, ("comprehensive_early_matched",))
                )
            elif cycle == 1:
                plans.append(
                    TargetPlan(
                        max(1, base - 1),
                        TargetZone.CONSOLIDATION,
                        ("comprehensive_early_consolidation",),
                    )
                )
            else:
                plans.append(
                    TargetPlan(
                        min(4, base + 1),
                        TargetZone.CHALLENGE,
                        ("comprehensive_bounded_challenge",),
                        False,
                        True,
                    )
                )
        return tuple(plans)

    challenge_slots = {
        "steady": {max(2, round(question_count * 0.65))},
        "standard": {
            max(2, round(question_count * 0.45)),
            max(2, round(question_count * 0.75)),
        },
        "challenge": {
            max(2, round(question_count * 0.30)),
            max(2, round(question_count * 0.55)),
            max(2, round(question_count * 0.80)),
        },
    }[preference]
    d5_unlocked = bool(
        accepted_challenge
        and subject_state.pending_conflict_count == 0
        and subject_state.reliable_first_attempt_count >= 20
        and subject_state.uncertainty <= 0.75
        and subject_state.theta >= difficulty_to_theta(4)
    )
    for position in range(1, question_count + 1):
        if position in {1, question_count}:
            plans.append(
                TargetPlan(
                    max(1, base - 1),
                    TargetZone.CONSOLIDATION,
                    ("positive_finish" if position == question_count else "round_consolidation",),
                )
            )
        elif position in challenge_slots:
            plans.append(
                TargetPlan(
                    5 if d5_unlocked else min(4, base + 1),
                    TargetZone.CHALLENGE,
                    ("comprehensive_scheduled_challenge",),
                    False,
                    True,
                )
            )
        else:
            plans.append(TargetPlan(base, TargetZone.MAIN, ("comprehensive_matched_training",)))
    return tuple(plans)


def _information_value(probability: float) -> float:
    # The four-option floor shifts the most discriminating practical region
    # upward; normalize Bernoulli variance around p=.625.
    return clamp((probability * (1.0 - probability)) / (0.625 * 0.375), 0.0, 1.0)


def _match_value(probability: float, zone: TargetZone) -> float:
    ideal = {
        TargetZone.CONSOLIDATION: 0.84,
        TargetZone.MAIN: 0.69,
        TargetZone.COVERAGE: 0.69,
        TargetZone.CHALLENGE: 0.50,
        TargetZone.DIAGNOSTIC: 0.625,
        TargetZone.VERIFY: 0.625,
    }[zone]
    return clamp(1.0 - abs(probability - ideal) / 0.45, 0.0, 1.0)


def score_candidate(
    candidate: Candidate,
    *,
    subject_theta: float,
    plan: TargetPlan,
    diagnostic_phase: bool,
    wrong_streak: int = 0,
    previous_was_challenge: bool = False,
) -> ScoredCandidate:
    if candidate.difficulty not in DIFFICULTY_THETA:
        raise ValueError("candidate difficulty must be between 1 and 5")
    effective_theta = subject_theta
    if candidate.topic_theta is not None:
        effective_theta, _ = shrink_topic_theta(
            subject_theta,
            candidate.topic_theta,
            candidate.topic_evidence,
        )
    probability = predict_correct_probability(
        effective_theta,
        difficulty=candidate.difficulty,
        item_b=candidate.empirical_difficulty,
    )
    quality = clamp(candidate.quality_weight, 0.0, 1.0)
    coverage = clamp(candidate.coverage_value, 0.0, 1.0)
    target_distance = clamp(1.0 - abs(candidate.difficulty - plan.difficulty) / 4.0, 0.0, 1.0)

    if diagnostic_phase:
        components = {
            "information": _information_value(probability),
            "quality": quality,
            "coverage": coverage,
            "boundary": 0.65 * target_distance
            + 0.20 * clamp(candidate.diagnostic_priority, 0.0, 1.0)
            + 0.15 * (1.0 if candidate.is_diagnostic_candidate else 0.0),
        }
        positive = (
            0.40 * components["information"]
            + 0.25 * components["quality"]
            + 0.20 * components["coverage"]
            + 0.15 * components["boundary"]
        )
    else:
        components = {
            "ability_match": 0.75 * _match_value(probability, plan.zone) + 0.25 * target_distance,
            "weak_topic": clamp(candidate.weak_topic_value, 0.0, 1.0),
            "due_review": clamp(candidate.due_review_value, 0.0, 1.0),
            "coverage": coverage,
            "quality": quality,
            "exploration": clamp(candidate.exploration_value, 0.0, 1.0),
        }
        positive = (
            0.35 * components["ability_match"]
            + 0.25 * components["weak_topic"]
            + 0.15 * components["due_review"]
            + 0.10 * components["coverage"]
            + 0.10 * components["quality"]
            + 0.05 * components["exploration"]
        )

    frustration = 0.0
    if wrong_streak >= 2 and candidate.difficulty > plan.difficulty:
        frustration = min(1.0, 0.4 + 0.2 * (wrong_streak - 2))
    consecutive_challenge = 1.0 if previous_was_challenge and plan.zone is TargetZone.CHALLENGE else 0.0
    penalties = {
        "recent_exposure": clamp(candidate.recent_exposure_penalty, 0.0, 1.0),
        "same_topic": clamp(candidate.same_topic_penalty, 0.0, 1.0),
        "same_type": clamp(candidate.same_type_penalty, 0.0, 1.0),
        "frustration": frustration,
        "consecutive_challenge": consecutive_challenge,
    }
    penalty = (
        0.30 * penalties["recent_exposure"]
        + 0.10 * penalties["same_topic"]
        + 0.05 * penalties["same_type"]
        + 0.25 * penalties["frustration"]
        + 0.20 * penalties["consecutive_challenge"]
    )
    score = clamp(positive - penalty, 0.0, 1.0)
    return ScoredCandidate(
        candidate=candidate,
        score=round(score, 6),
        predicted_probability=round(probability, 6),
        score_components={
            **{key: round(value, 6) for key, value in components.items()},
            **{f"penalty_{key}": round(value, 6) for key, value in penalties.items()},
        },
    )


def select_top_k_weighted(
    candidates: Iterable[ScoredCandidate],
    *,
    seed: str,
    top_k: int = 5,
) -> ScoredCandidate:
    """Select reproducibly from the best candidates without hotspot lock-in."""

    ranked = sorted(candidates, key=lambda item: (-item.score, item.candidate.question_id))
    if not ranked:
        raise ValueError("at least one candidate is required")
    shortlist = ranked[: max(1, min(int(top_k), len(ranked)))]
    digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    floor = min(item.score for item in shortlist)
    weights = [max(0.05, item.score - floor + 0.05) for item in shortlist]
    return rng.choices(shortlist, weights=weights, k=1)[0]


def level_range(theta: float, uncertainty: float) -> tuple[int, int]:
    lower = theta_to_difficulty(float(theta) - max(0.0, float(uncertainty)) / 2.0)
    upper = theta_to_difficulty(float(theta) + max(0.0, float(uncertainty)) / 2.0)
    return min(lower, upper), max(lower, upper)


def confidence_label(state: AbilityState) -> str:
    if state.diagnostic_status is DiagnosticStatus.STABLE:
        return "稳定"
    if state.pending_conflict_count:
        return "待复验"
    if state.reliable_first_attempt_count < 8:
        return "初步"
    return "正在变稳"
