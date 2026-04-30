from __future__ import annotations

from dataclasses import dataclass

from models.motion_definition import MotionDefinition


@dataclass(slots=True)
class TemporalMetrics:
    values: dict[str, float]


class TemporalAnalyzer:
    """
    时序分析器。

    当前支持：
    - sit_up:
        motion_phase, rep_counter, rep_cycle_duration, knee_angle_variation, quality_score
    - bridge:
        motion_phase, ascent_duration, peak_hold_duration, descent_duration,
        hip_angular_velocity, trajectory_consistency, ahp_quality_score
    """

    SIT_UP_PREPARE = 0.0
    SIT_UP_CONCENTRIC = 1.0
    SIT_UP_PEAK = 2.0
    SIT_UP_ECCENTRIC = 3.0
    SIT_UP_COMPLETE = 4.0

    BRIDGE_PREPARE = 0.0
    BRIDGE_ASCENT = 1.0
    BRIDGE_PEAK = 2.0
    BRIDGE_DESCENT = 3.0
    BRIDGE_COMPLETE = 4.0

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._sit_up_rep_counter = 0
        self._sit_up_last_rep_cycle_duration_s = 0.0
        self._sit_up_last_phase = self.SIT_UP_PREPARE
        self._sit_up_rep_start_timestamp_ms: int | None = None
        self._sit_up_peak_reached = False
        self._sit_up_baseline_left_knee: float | None = None
        self._sit_up_baseline_right_knee: float | None = None

        self._bridge_last_phase = self.BRIDGE_PREPARE
        self._bridge_last_hip_angle: float | None = None
        self._bridge_last_timestamp_ms: int | None = None

        self._bridge_ascent_start_ms: int | None = None
        self._bridge_peak_start_ms: int | None = None
        self._bridge_descent_start_ms: int | None = None

        self._bridge_last_ascent_duration_s = 0.0
        self._bridge_last_peak_hold_duration_s = 0.0
        self._bridge_last_descent_duration_s = 0.0
        self._bridge_last_hip_angular_velocity = 0.0

        self._bridge_hip_y_history: list[float] = []
        self._bridge_last_trajectory_consistency = 0.0

    def calculate(
        self,
        motion_definition: MotionDefinition,
        base_metrics: dict[str, float],
        timestamp_ms: int,
    ) -> TemporalMetrics:
        if motion_definition.motion_id == "sit_up":
            return self._calculate_sit_up_metrics(base_metrics, timestamp_ms)

        if motion_definition.motion_id == "bridge":
            return self._calculate_bridge_metrics(base_metrics, timestamp_ms)

        return TemporalMetrics(values={})

    # =========================
    # sit_up
    # =========================
    def _calculate_sit_up_metrics(
        self,
        base_metrics: dict[str, float],
        timestamp_ms: int,
    ) -> TemporalMetrics:
        trunk_ground_angle = base_metrics.get("trunk_ground_angle", 0.0)
        left_knee = base_metrics.get("left_knee", 0.0)
        right_knee = base_metrics.get("right_knee", 0.0)
        neck_flexion_angle = base_metrics.get("neck_flexion_angle", 0.0)
        lumbar_gap_distance = base_metrics.get("lumbar_gap_distance", 0.0)

        knee_angle_variation = self._calculate_sit_up_knee_angle_variation(
            left_knee=left_knee,
            right_knee=right_knee,
        )

        is_prepare_pose = self._is_sit_up_prepare_pose(
            trunk_ground_angle=trunk_ground_angle,
            left_knee=left_knee,
            right_knee=right_knee,
        )

        if is_prepare_pose:
            if self._sit_up_baseline_left_knee is None:
                self._sit_up_baseline_left_knee = left_knee
            if self._sit_up_baseline_right_knee is None:
                self._sit_up_baseline_right_knee = right_knee

        current_phase = self._resolve_sit_up_phase(
            trunk_ground_angle=trunk_ground_angle,
            is_prepare_pose=is_prepare_pose,
        )

        if self._sit_up_last_phase == self.SIT_UP_PREPARE and current_phase == self.SIT_UP_CONCENTRIC:
            self._sit_up_rep_start_timestamp_ms = timestamp_ms
            self._sit_up_peak_reached = False

        if current_phase == self.SIT_UP_PEAK and 30.0 <= trunk_ground_angle <= 60.0:
            self._sit_up_peak_reached = True

        if (
            self._sit_up_last_phase in (
                self.SIT_UP_CONCENTRIC,
                self.SIT_UP_PEAK,
                self.SIT_UP_ECCENTRIC,
            )
            and current_phase == self.SIT_UP_COMPLETE
            and self._sit_up_peak_reached
        ):
            self._sit_up_rep_counter += 1

            if self._sit_up_rep_start_timestamp_ms is not None:
                self._sit_up_last_rep_cycle_duration_s = (
                    timestamp_ms - self._sit_up_rep_start_timestamp_ms
                ) / 1000.0

            current_phase = self.SIT_UP_PREPARE
            self._sit_up_rep_start_timestamp_ms = None
            self._sit_up_peak_reached = False

        self._sit_up_last_phase = current_phase

        quality_score = self._calculate_sit_up_quality_score(
            trunk_ground_angle=trunk_ground_angle,
            rep_cycle_duration=self._sit_up_last_rep_cycle_duration_s,
            knee_angle_variation=knee_angle_variation,
            neck_flexion_angle=neck_flexion_angle,
            lumbar_gap_distance=lumbar_gap_distance,
        )

        return TemporalMetrics(
            values={
                "motion_phase": current_phase,
                "rep_counter": float(self._sit_up_rep_counter),
                "rep_cycle_duration": self._sit_up_last_rep_cycle_duration_s,
                "knee_angle_variation": knee_angle_variation,
                "quality_score": quality_score,
            }
        )

    def _is_sit_up_prepare_pose(
        self,
        trunk_ground_angle: float,
        left_knee: float,
        right_knee: float,
    ) -> bool:
        left_ok = 85.0 <= left_knee <= 95.0
        right_ok = 85.0 <= right_knee <= 95.0
        trunk_ok = trunk_ground_angle <= 5.0
        return left_ok and right_ok and trunk_ok

    def _resolve_sit_up_phase(
        self,
        trunk_ground_angle: float,
        is_prepare_pose: bool,
    ) -> float:
        if is_prepare_pose:
            if self._sit_up_last_phase in (
                self.SIT_UP_CONCENTRIC,
                self.SIT_UP_PEAK,
                self.SIT_UP_ECCENTRIC,
            ):
                return self.SIT_UP_COMPLETE
            return self.SIT_UP_PREPARE

        if 5.0 < trunk_ground_angle < 30.0:
            if self._sit_up_last_phase in (self.SIT_UP_PEAK, self.SIT_UP_ECCENTRIC):
                return self.SIT_UP_ECCENTRIC
            return self.SIT_UP_CONCENTRIC

        if 30.0 <= trunk_ground_angle <= 60.0:
            return self.SIT_UP_PEAK

        if trunk_ground_angle > 60.0:
            return self.SIT_UP_PEAK

        return self.SIT_UP_PREPARE

    def _calculate_sit_up_knee_angle_variation(
        self,
        left_knee: float,
        right_knee: float,
    ) -> float:
        if self._sit_up_baseline_left_knee is None or self._sit_up_baseline_right_knee is None:
            return 0.0

        left_delta = abs(left_knee - self._sit_up_baseline_left_knee)
        right_delta = abs(right_knee - self._sit_up_baseline_right_knee)
        return (left_delta + right_delta) / 2.0

    def _calculate_sit_up_quality_score(
        self,
        trunk_ground_angle: float,
        rep_cycle_duration: float,
        knee_angle_variation: float,
        neck_flexion_angle: float,
        lumbar_gap_distance: float,
    ) -> float:
        """
        sit_up 综合评分，满分 100。
        """
        if neck_flexion_angle > 35.0:
            return 0.0

        if lumbar_gap_distance > 0.08:
            return 0.0

        if trunk_ground_angle < 30.0:
            return 0.0

        speed_score = 100.0
        if rep_cycle_duration > 0.0:
            if rep_cycle_duration < 1.2:
                speed_score = 40.0
            elif rep_cycle_duration < 1.6:
                speed_score = 70.0
            elif rep_cycle_duration <= 3.0:
                speed_score = 100.0
            else:
                speed_score = 80.0

        leg_score = 100.0
        if knee_angle_variation > 30.0:
            leg_score = 40.0
        elif knee_angle_variation > 20.0:
            leg_score = 70.0
        elif knee_angle_variation > 15.0:
            leg_score = 85.0

        range_score = 100.0
        if trunk_ground_angle > 60.0:
            range_score = 70.0
        elif trunk_ground_angle > 45.0:
            range_score = 90.0
        elif 30.0 <= trunk_ground_angle <= 45.0:
            range_score = 100.0

        score = speed_score * 0.5 + leg_score * 0.3 + range_score * 0.2
        return round(score, 2)

    # =========================
    # bridge
    # =========================
    def _calculate_bridge_metrics(
        self,
        base_metrics: dict[str, float],
        timestamp_ms: int,
    ) -> TemporalMetrics:
        left_hip = base_metrics.get("left_hip", 0.0)
        right_hip = base_metrics.get("right_hip", 0.0)
        pelvis_tilt = base_metrics.get("pelvis_tilt", 0.0)

        hip_angle = (left_hip + right_hip) / 2.0
        current_phase = self._resolve_bridge_phase(hip_angle)

        if self._bridge_last_timestamp_ms is not None and self._bridge_last_hip_angle is not None:
            dt_s = max((timestamp_ms - self._bridge_last_timestamp_ms) / 1000.0, 1e-6)
            self._bridge_last_hip_angular_velocity = abs(
                hip_angle - self._bridge_last_hip_angle
            ) / dt_s

        if self._bridge_last_phase == self.BRIDGE_PREPARE and current_phase == self.BRIDGE_ASCENT:
            self._bridge_ascent_start_ms = timestamp_ms

        if self._bridge_last_phase == self.BRIDGE_ASCENT and current_phase == self.BRIDGE_PEAK:
            if self._bridge_ascent_start_ms is not None:
                self._bridge_last_ascent_duration_s = (
                    timestamp_ms - self._bridge_ascent_start_ms
                ) / 1000.0
            self._bridge_peak_start_ms = timestamp_ms

        if self._bridge_last_phase == self.BRIDGE_PEAK and current_phase == self.BRIDGE_DESCENT:
            if self._bridge_peak_start_ms is not None:
                self._bridge_last_peak_hold_duration_s = (
                    timestamp_ms - self._bridge_peak_start_ms
                ) / 1000.0
            self._bridge_descent_start_ms = timestamp_ms

        if self._bridge_last_phase == self.BRIDGE_DESCENT and current_phase == self.BRIDGE_COMPLETE:
            if self._bridge_descent_start_ms is not None:
                self._bridge_last_descent_duration_s = (
                    timestamp_ms - self._bridge_descent_start_ms
                ) / 1000.0
            current_phase = self.BRIDGE_PREPARE

        hip_mid_y_proxy = hip_angle
        self._bridge_hip_y_history.append(hip_mid_y_proxy)
        if len(self._bridge_hip_y_history) > 10:
            self._bridge_hip_y_history.pop(0)

        if len(self._bridge_hip_y_history) >= 2:
            diffs = [
                abs(self._bridge_hip_y_history[i] - self._bridge_hip_y_history[i - 1])
                for i in range(1, len(self._bridge_hip_y_history))
            ]
            self._bridge_last_trajectory_consistency = sum(diffs) / len(diffs)

        self._bridge_last_phase = current_phase
        self._bridge_last_timestamp_ms = timestamp_ms
        self._bridge_last_hip_angle = hip_angle

        ahp_quality_score = self._calculate_bridge_ahp_quality_score(
            left_hip=left_hip,
            right_hip=right_hip,
            pelvis_tilt=pelvis_tilt,
            ascent_duration=self._bridge_last_ascent_duration_s,
            peak_hold_duration=self._bridge_last_peak_hold_duration_s,
            descent_duration=self._bridge_last_descent_duration_s,
            hip_angular_velocity=self._bridge_last_hip_angular_velocity,
            trajectory_consistency=self._bridge_last_trajectory_consistency,
        )

        return TemporalMetrics(
            values={
                "motion_phase": current_phase,
                "ascent_duration": self._bridge_last_ascent_duration_s,
                "peak_hold_duration": self._bridge_last_peak_hold_duration_s,
                "descent_duration": self._bridge_last_descent_duration_s,
                "hip_angular_velocity": self._bridge_last_hip_angular_velocity,
                "trajectory_consistency": self._bridge_last_trajectory_consistency,
                "ahp_quality_score": ahp_quality_score,
            }
        )

    def _resolve_bridge_phase(self, hip_angle: float) -> float:
        if hip_angle < 140.0:
            if self._bridge_last_phase in (self.BRIDGE_ASCENT, self.BRIDGE_PEAK, self.BRIDGE_DESCENT):
                return self.BRIDGE_COMPLETE
            return self.BRIDGE_PREPARE

        if 140.0 <= hip_angle < 160.0:
            if self._bridge_last_phase in (self.BRIDGE_PEAK, self.BRIDGE_DESCENT):
                return self.BRIDGE_DESCENT
            return self.BRIDGE_ASCENT

        return self.BRIDGE_PEAK

    def _calculate_bridge_ahp_quality_score(
        self,
        left_hip: float,
        right_hip: float,
        pelvis_tilt: float,
        ascent_duration: float,
        peak_hold_duration: float,
        descent_duration: float,
        hip_angular_velocity: float,
        trajectory_consistency: float,
    ) -> float:
        """
        bridge AHP 风格综合评分，满分 100。
        """
        hip_extension_score = 100.0
        hip_mean = (left_hip + right_hip) / 2.0
        if hip_mean < 135.0:
            hip_extension_score = 40.0
        elif hip_mean < 150.0:
            hip_extension_score = 70.0
        elif hip_mean < 160.0:
            hip_extension_score = 85.0

        pelvic_stability_score = 100.0
        pelvis_abs = abs(pelvis_tilt)
        if pelvis_abs > 0.12:
            pelvic_stability_score = 40.0
        elif pelvis_abs > 0.08:
            pelvic_stability_score = 70.0
        elif pelvis_abs > 0.05:
            pelvic_stability_score = 85.0

        timing_control_score = 100.0
        timing_penalty_count = 0
        if ascent_duration > 0.0 and not (1.5 <= ascent_duration <= 2.0):
            timing_penalty_count += 1
        if peak_hold_duration > 0.0 and not (1.0 <= peak_hold_duration <= 2.0):
            timing_penalty_count += 1
        if descent_duration > 0.0 and not (1.2 <= descent_duration <= 2.0):
            timing_penalty_count += 1
        if hip_angular_velocity > 100.0:
            timing_penalty_count += 2
        elif hip_angular_velocity > 70.0:
            timing_penalty_count += 1

        if timing_penalty_count >= 3:
            timing_control_score = 40.0
        elif timing_penalty_count == 2:
            timing_control_score = 70.0
        elif timing_penalty_count == 1:
            timing_control_score = 85.0

        trajectory_score = 100.0
        if trajectory_consistency > 12.0:
            trajectory_score = 40.0
        elif trajectory_consistency > 8.0:
            trajectory_score = 70.0
        elif trajectory_consistency > 5.0:
            trajectory_score = 85.0

        score = (
            hip_extension_score * 0.4
            + pelvic_stability_score * 0.3
            + timing_control_score * 0.2
            + trajectory_score * 0.1
        )
        return round(score, 2)