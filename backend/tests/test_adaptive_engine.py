from __future__ import annotations

import unittest

from app.services.adaptive_engine import (
    AbilityState,
    Candidate,
    DiagnosticStatus,
    EvidenceContext,
    Observation,
    TargetPlan,
    TargetZone,
    can_unlock_d5,
    compute_evidence_weight,
    detect_inversion,
    plan_comprehensive_targets,
    plan_next_target,
    predict_correct_probability,
    score_candidate,
    select_top_k_weighted,
    shrink_topic_theta,
    update_ability,
    validate_scope,
)


def observation(
    question_id: str,
    difficulty: int,
    is_correct: bool,
    *,
    position: int,
    module: str = "演绎推理",
    submodule: str = "充分条件",
    question_type: str = "single_choice",
    weight: float = 1.0,
    first: bool = True,
) -> Observation:
    return Observation(
        question_id=question_id,
        difficulty=difficulty,
        is_correct=is_correct,
        module=module,
        submodule=submodule,
        question_type=question_type,
        evidence_weight=weight,
        is_first_attempt=first,
        position=position,
    )


class AdaptiveScopeTests(unittest.TestCase):
    def test_each_exam_accepts_only_its_three_subjects(self):
        self.assertEqual(validate_scope("z001", "中华文化"), ("Z001", "中华文化"))
        self.assertEqual(validate_scope("Z001", "英语运用"), ("Z001", "英语运用"))
        self.assertEqual(validate_scope("Z001", "逻辑推理"), ("Z001", "逻辑推理"))
        self.assertEqual(validate_scope("Z002", "数学基础"), ("Z002", "数学基础"))
        with self.assertRaises(ValueError):
            validate_scope("Z001", "数学基础")
        with self.assertRaises(ValueError):
            validate_scope("Z002", "逻辑推理")

    def test_common_subject_states_are_still_driven_by_the_requested_exam_scope(self):
        # The engine never owns a global COMMON ability state.  The caller must
        # resolve a public question to the user's actual Z001/Z002 scope first.
        with self.assertRaises(ValueError):
            validate_scope("COMMON", "英语运用")


class AdaptiveEvidenceTests(unittest.TestCase):
    def test_probability_is_monotonic_in_ability_and_difficulty(self):
        self.assertGreater(
            predict_correct_probability(1.0, difficulty=3),
            predict_correct_probability(-1.0, difficulty=3),
        )
        self.assertGreater(
            predict_correct_probability(0.0, difficulty=1),
            predict_correct_probability(0.0, difficulty=5),
        )

    def test_repeat_and_extreme_duration_are_soft_weighted(self):
        repeat = compute_evidence_weight(EvidenceContext(is_first_attempt=False))
        extreme = compute_evidence_weight(
            EvidenceContext(is_first_attempt=True, used_time=2, estimated_time=30)
        )
        self.assertEqual(repeat.weight, 0.25)
        self.assertFalse(repeat.reliable_first_attempt)
        self.assertEqual(extreme.weight, 0.5)
        self.assertFalse(extreme.reliable_first_attempt)

    def test_seen_answer_and_invalid_question_have_zero_weight(self):
        self.assertEqual(compute_evidence_weight(EvidenceContext(answer_seen=True)).weight, 0.0)
        self.assertEqual(compute_evidence_weight(EvidenceContext(question_valid=False)).weight, 0.0)

    def test_topic_estimate_shrinks_toward_its_subject(self):
        sparse, sparse_lambda = shrink_topic_theta(1.0, -1.0, 1.0)
        mature, mature_lambda = shrink_topic_theta(1.0, -1.0, 80.0)
        self.assertGreater(sparse, mature)
        self.assertLess(sparse_lambda, mature_lambda)

    def test_bounded_update_moves_only_from_the_state_passed_to_it(self):
        reliable = compute_evidence_weight(EvidenceContext())
        strong_subject = AbilityState(theta=1.1, effective_evidence=10)
        weak_subject = AbilityState(theta=-1.1, effective_evidence=10)
        topic = AbilityState()

        strong_after = update_ability(
            strong_subject,
            topic,
            difficulty=4,
            is_correct=True,
            evidence=reliable,
        ).subject_after
        weak_after = update_ability(
            weak_subject,
            topic,
            difficulty=1,
            is_correct=False,
            evidence=reliable,
        ).subject_after

        self.assertGreater(strong_after.theta, strong_subject.theta)
        self.assertLess(weak_after.theta, weak_subject.theta)
        self.assertLessEqual(strong_after.theta - strong_subject.theta, 0.25)
        self.assertLessEqual(weak_subject.theta - weak_after.theta, 0.25)

    def test_twenty_reliable_answers_can_reach_stable(self):
        reliable = compute_evidence_weight(EvidenceContext())
        subject = AbilityState()
        topic = AbilityState()
        for _ in range(20):
            result = update_ability(
                subject,
                topic,
                difficulty=3,
                is_correct=True,
                evidence=reliable,
            )
            subject, topic = result.subject_after, result.topic_after
        self.assertEqual(subject.reliable_first_attempt_count, 20)
        self.assertEqual(subject.diagnostic_status, DiagnosticStatus.STABLE)

    def test_twenty_answers_without_topic_coverage_remain_calibrating(self):
        reliable = compute_evidence_weight(EvidenceContext())
        subject = AbilityState()
        topic = AbilityState()
        for _ in range(20):
            result = update_ability(
                subject,
                topic,
                difficulty=3,
                is_correct=True,
                evidence=reliable,
                subject_coverage_ready=False,
            )
            subject, topic = result.subject_after, result.topic_after
        self.assertEqual(subject.reliable_first_attempt_count, 20)
        self.assertEqual(subject.diagnostic_status, DiagnosticStatus.CALIBRATING)


class AdaptiveConflictTests(unittest.TestCase):
    def test_only_same_skill_reliable_first_attempts_create_an_inversion(self):
        low_wrong = observation("low", 1, False, position=1)
        high_right = observation("high", 3, True, position=2)
        inversion = detect_inversion([low_wrong, high_right])
        self.assertIsNotNone(inversion)
        self.assertEqual(inversion.difficulty_gap, 2)

        other_topic = observation(
            "other", 4, True, position=2, submodule="必要条件"
        )
        self.assertIsNone(detect_inversion([low_wrong, other_topic]))
        self.assertIsNone(
            detect_inversion([low_wrong, observation("repeat", 4, True, position=2, first=False)])
        )

    def test_inversion_preserves_answer_weight_but_raises_uncertainty(self):
        reliable = compute_evidence_weight(EvidenceContext())
        before = AbilityState(
            theta=0.2,
            uncertainty=0.8,
            effective_evidence=10,
            reliable_first_attempt_count=10,
            diagnostic_status=DiagnosticStatus.CALIBRATING,
        )
        result = update_ability(
            before,
            AbilityState(theta=0.2),
            difficulty=4,
            is_correct=True,
            evidence=reliable,
            inversion_pending=True,
        )
        self.assertEqual(result.evidence_weight, 1.0)
        self.assertEqual(result.subject_after.pending_conflict_count, 1)
        self.assertGreater(result.subject_after.uncertainty, before.uncertainty)
        self.assertEqual(result.subject_after.diagnostic_status, DiagnosticStatus.VERIFYING)

    def test_stable_user_remains_recalibrating_while_conflict_is_pending(self):
        reliable = compute_evidence_weight(EvidenceContext())
        before = AbilityState(
            theta=0.8,
            uncertainty=0.6,
            effective_evidence=30,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        first = update_ability(
            before,
            AbilityState(theta=0.8),
            difficulty=4,
            is_correct=True,
            evidence=reliable,
            inversion_pending=True,
        ).subject_after
        second = update_ability(
            first,
            AbilityState(theta=0.8),
            difficulty=2,
            is_correct=True,
            evidence=reliable,
        ).subject_after
        self.assertEqual(first.diagnostic_status, DiagnosticStatus.RECALIBRATING)
        self.assertEqual(second.diagnostic_status, DiagnosticStatus.RECALIBRATING)


class AdaptiveSequenceTests(unittest.TestCase):
    def test_new_user_starts_at_d2_and_second_item_branches(self):
        state = AbilityState()
        first = plan_next_target(position=1, subject_state=state, observations=[])
        self.assertEqual((first.difficulty, first.zone), (2, TargetZone.DIAGNOSTIC))

        after_right = plan_next_target(
            position=2,
            subject_state=state,
            observations=[observation("q1", 2, True, position=1)],
        )
        after_wrong = plan_next_target(
            position=2,
            subject_state=state,
            observations=[observation("q1", 2, False, position=1)],
        )
        self.assertEqual(after_right.difficulty, 3)
        self.assertEqual(after_wrong.difficulty, 1)

    def test_skipped_early_items_keep_a_neutral_probe(self):
        state = AbilityState()
        plan = plan_next_target(
            position=3,
            subject_state=state,
            observations=[],
        )
        self.assertEqual((plan.difficulty, plan.zone), (2, TargetZone.DIAGNOSTIC))
        self.assertEqual(plan.reason_codes, ("confirm_initial_boundary",))

    def test_all_eight_slots_remain_in_the_warmup_flow(self):
        # After four reliable answers the state becomes CALIBRATING, but slots
        # five through eight still belong to the user's fixed smart warm-up.
        state = AbilityState(
            theta=0.2,
            reliable_first_attempt_count=4,
            diagnostic_status=DiagnosticStatus.CALIBRATING,
        )
        previous = [
            observation("q1", 2, True, position=1),
            observation("q2", 3, True, position=2),
            observation("q3", 4, False, position=3),
            observation("q4", 3, True, position=4),
        ]
        fifth = plan_next_target(position=5, subject_state=state, observations=previous)
        eighth = plan_next_target(position=8, subject_state=state, observations=previous)
        self.assertIn("complete_warmup_difficulty_coverage", fifth.reason_codes)
        self.assertEqual(eighth.reason_codes, ("positive_finish",))

    def test_pending_conflict_resumes_verification_at_start_of_new_session(self):
        state = AbilityState(
            reliable_first_attempt_count=6,
            diagnostic_status=DiagnosticStatus.VERIFYING,
            pending_conflict_count=1,
        )
        first = plan_next_target(position=1, subject_state=state, observations=[])
        second = plan_next_target(
            position=2,
            subject_state=state,
            observations=[],
            pending_verification_count=1,
        )
        self.assertEqual((first.zone, first.difficulty), (TargetZone.VERIFY, 2))
        self.assertEqual((second.zone, second.difficulty), (TargetZone.VERIFY, 3))

    def test_verification_is_interleaved_and_also_applies_to_stable_users(self):
        state = AbilityState(
            theta=0.8,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.RECALIBRATING,
            pending_conflict_count=1,
        )
        verify = plan_next_target(
            position=5,
            subject_state=state,
            observations=[],
            pending_verification_count=1,
        )
        filler = plan_next_target(
            position=6,
            subject_state=state,
            observations=[],
            pending_verification_count=1,
            previous_was_verification=True,
        )
        self.assertEqual((verify.zone, verify.difficulty), (TargetZone.VERIFY, 3))
        self.assertEqual(filler.zone, TargetZone.COVERAGE)
        self.assertEqual(filler.reason_codes, ("verification_interleave",))

    def test_persistence_can_pause_a_stale_or_out_of_scope_verification(self):
        state = AbilityState(
            theta=0.4,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.RECALIBRATING,
            pending_conflict_count=1,
        )
        plan = plan_next_target(
            position=3,
            subject_state=state,
            observations=[
                observation("low", 1, False, position=1),
                observation("high", 3, True, position=2),
            ],
            pending_verification=False,
        )
        self.assertIsNot(plan.zone, TargetZone.VERIFY)

    def test_stable_session_never_ends_on_a_challenge_slot(self):
        state = AbilityState(
            theta=0.8,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        plan = plan_next_target(
            position=5,
            question_count=5,
            subject_state=state,
            observations=[
                observation("q1", 3, True, position=1),
                observation("q2", 3, True, position=2),
                observation("q3", 4, True, position=3),
            ],
        )
        self.assertEqual((plan.zone, plan.difficulty), (TargetZone.CONSOLIDATION, 3))
        self.assertEqual(plan.reason_codes, ("positive_finish",))
        self.assertFalse(plan.is_challenge)

    def test_final_slot_defers_pending_verification_to_the_next_session(self):
        state = AbilityState(
            theta=0.8,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.RECALIBRATING,
            pending_conflict_count=1,
        )
        final = plan_next_target(
            position=5,
            question_count=5,
            subject_state=state,
            observations=[],
            pending_verification_count=1,
        )
        resumed = plan_next_target(
            position=1,
            question_count=5,
            subject_state=state,
            observations=[],
            pending_verification_count=1,
        )

        self.assertEqual((final.zone, final.difficulty), (TargetZone.CONSOLIDATION, 3))
        self.assertEqual(final.reason_codes, ("positive_finish",))
        self.assertFalse(final.is_diagnostic)
        self.assertEqual(state.pending_conflict_count, 1)
        self.assertEqual(resumed.zone, TargetZone.VERIFY)

    def test_weak_learner_final_slot_uses_an_easier_recovery_item(self):
        state = AbilityState(
            theta=-0.8,
            reliable_first_attempt_count=12,
            diagnostic_status=DiagnosticStatus.CALIBRATING,
        )
        plan = plan_next_target(
            position=5,
            question_count=5,
            subject_state=state,
            observations=[
                observation("q1", 1, True, position=1),
                observation("q2", 2, True, position=2),
                observation("q3", 2, True, position=3),
            ],
        )

        self.assertEqual((plan.zone, plan.difficulty), (TargetZone.CONSOLIDATION, 1))
        self.assertEqual(plan.reason_codes, ("positive_finish",))
        self.assertFalse(plan.is_challenge)

    def test_short_cold_start_cannot_end_on_uncovered_challenge_level(self):
        plan = plan_next_target(
            position=5,
            question_count=5,
            subject_state=AbilityState(),
            observations=[
                observation("q1", 2, True, position=1),
                observation("q2", 1, True, position=2),
                observation("q3", 3, True, position=3),
            ],
        )

        self.assertEqual((plan.zone, plan.difficulty), (TargetZone.CONSOLIDATION, 2))
        self.assertEqual(plan.reason_codes, ("positive_finish",))
        self.assertFalse(plan.is_challenge)

    def test_two_wrong_answers_force_consolidation(self):
        state = AbilityState(
            theta=0.8,
            reliable_first_attempt_count=25,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        plan = plan_next_target(
            position=6,
            subject_state=state,
            observations=[
                observation("q1", 4, False, position=1),
                observation("q2", 4, False, position=2),
            ],
        )
        self.assertEqual(plan.zone, TargetZone.CONSOLIDATION)
        self.assertLess(plan.difficulty, 4)

    def test_a_challenge_is_always_followed_by_recovery(self):
        state = AbilityState(
            theta=0.8,
            reliable_first_attempt_count=25,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        previous = [
            observation("q1", 3, True, position=1),
            observation("q2", 3, True, position=2),
            observation("q3", 4, True, position=3),
        ]
        plan = plan_next_target(
            position=4,
            subject_state=state,
            observations=previous,
            previous_was_challenge=True,
        )
        self.assertFalse(plan.is_challenge)
        self.assertEqual(plan.zone, TargetZone.CONSOLIDATION)
        self.assertEqual(plan.difficulty, 3)
        self.assertEqual(plan.reason_codes, ("challenge_recovery",))

    def test_d5_requires_d3_and_two_distinct_d4_confirmations(self):
        d3_d4_d5 = [
            observation("d3", 3, True, position=1),
            observation("d4", 4, True, position=2),
            observation("d5", 5, True, position=3),
        ]
        self.assertFalse(can_unlock_d5(d3_d4_d5, accepted_challenge=True))

        qualified = [
            *d3_d4_d5[:2],
            observation("d4-second", 4, True, position=3),
        ]
        self.assertTrue(can_unlock_d5(qualified, accepted_challenge=True))
        self.assertFalse(can_unlock_d5(qualified, accepted_challenge=True, pending_conflicts=1))

    def test_high_theta_does_not_bypass_the_d5_challenge_gate(self):
        state = AbilityState(
            theta=3.0,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        ordinary = plan_next_target(
            position=2,
            subject_state=state,
            observations=[],
            preference="standard",
        )
        self.assertEqual((ordinary.difficulty, ordinary.zone), (4, TargetZone.MAIN))
        self.assertFalse(ordinary.is_challenge)

        qualified = [
            observation("d3", 3, True, position=1),
            observation("d4-a", 4, True, position=2),
            observation("d4-b", 4, True, position=3),
        ]
        challenge = plan_next_target(
            position=5,
            subject_state=state,
            observations=qualified,
            preference="challenge",
            accepted_challenge=True,
        )
        self.assertEqual((challenge.difficulty, challenge.zone), (5, TargetZone.CHALLENGE))
        self.assertTrue(challenge.is_challenge)


class AdaptiveComprehensivePlanTests(unittest.TestCase):
    def test_cold_start_fixed_round_covers_d1_through_d4_before_feedback(self):
        plans = plan_comprehensive_targets(
            subject_state=AbilityState(
                diagnostic_status=DiagnosticStatus.NEW,
                reliable_first_attempt_count=0,
            ),
            question_count=8,
        )

        self.assertEqual([plan.difficulty for plan in plans[:4]], [2, 3, 1, 4])
        self.assertTrue(all(plan.is_diagnostic for plan in plans[:4]))
        self.assertEqual(plans[-1].zone, TargetZone.CONSOLIDATION)
        self.assertLessEqual(plans[-1].difficulty, 2)

    def test_established_comprehensive_round_is_fixed_and_ends_safely(self):
        state = AbilityState(
            theta=1.0,
            uncertainty=0.6,
            reliable_first_attempt_count=30,
            diagnostic_status=DiagnosticStatus.STABLE,
        )
        plans = plan_comprehensive_targets(
            subject_state=state,
            question_count=10,
            preference="standard",
        )

        self.assertEqual(len(plans), 10)
        self.assertEqual(plans[0].zone, TargetZone.CONSOLIDATION)
        self.assertEqual(plans[-1].zone, TargetZone.CONSOLIDATION)
        self.assertTrue(any(plan.zone is TargetZone.CHALLENGE for plan in plans))
        self.assertTrue(all(plan.zone is not TargetZone.VERIFY for plan in plans))


class AdaptiveRankingTests(unittest.TestCase):
    def test_top_k_selection_is_reproducible_and_never_leaves_shortlist(self):
        plan = TargetPlan(3, TargetZone.MAIN, ("matched_training",))
        scored = [
            score_candidate(
                Candidate(
                    question_id=f"q{index}",
                    difficulty=3,
                    module="语言知识",
                    submodule="词汇",
                    quality_weight=max(0.1, 1.0 - index / 10),
                ),
                subject_theta=0,
                plan=plan,
                diagnostic_phase=False,
            )
            for index in range(10)
        ]
        first = select_top_k_weighted(scored, seed="session:5", top_k=5)
        second = select_top_k_weighted(reversed(scored), seed="session:5", top_k=5)
        top_ids = {
            item.candidate.question_id
            for item in sorted(scored, key=lambda item: (-item.score, item.candidate.question_id))[:5]
        }
        self.assertEqual(first.candidate.question_id, second.candidate.question_id)
        self.assertIn(first.candidate.question_id, top_ids)

    def test_recent_exposure_is_penalized(self):
        plan = TargetPlan(3, TargetZone.MAIN, ("matched_training",))
        fresh = Candidate("fresh", 3, "语言知识", "语法")
        repeated = Candidate("repeat", 3, "语言知识", "语法", recent_exposure_penalty=1.0)
        fresh_score = score_candidate(
            fresh, subject_theta=0, plan=plan, diagnostic_phase=False
        ).score
        repeated_score = score_candidate(
            repeated, subject_theta=0, plan=plan, diagnostic_phase=False
        ).score
        self.assertGreater(fresh_score, repeated_score)


if __name__ == "__main__":
    unittest.main()
