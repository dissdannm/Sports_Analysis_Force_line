# output/skeleton_drawer.py

from __future__ import annotations

import cv2

from models.landmarks import PoseLandmarks


class SkeletonDrawer:
    """
    骨架绘制器。

    设计定位：
    - 用于本地调试和演示
    - 负责在图像上绘制关键点和骨架连线
    - 不负责角度文字、告警信息或其他业务内容

    当前绘制范围：
    - 头部关键点（仅 nose）
    - 肩、肘、腕
    - 髋、膝、踝、足跟、足尖
    - 肩线、髋线、躯干连接线
    """

    CONNECTIONS = [
        # 躯干
        ("left_shoulder", "right_shoulder"),
        ("left_shoulder", "left_hip"),
        ("right_shoulder", "right_hip"),
        ("left_hip", "right_hip"),

        # 左上肢
        ("left_shoulder", "left_elbow"),
        ("left_elbow", "left_wrist"),

        # 右上肢
        ("right_shoulder", "right_elbow"),
        ("right_elbow", "right_wrist"),

        # 左下肢
        ("left_hip", "left_knee"),
        ("left_knee", "left_ankle"),
        ("left_ankle", "left_heel"),
        ("left_heel", "left_foot_index"),

        # 右下肢
        ("right_hip", "right_knee"),
        ("right_knee", "right_ankle"),
        ("right_ankle", "right_heel"),
        ("right_heel", "right_foot_index"),
    ]

    POINT_NAMES = [
        "nose",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
        "left_heel",
        "right_heel",
        "left_foot_index",
        "right_foot_index",
    ]

    def __init__(
        self,
        line_color: tuple[int, int, int] = (0, 255, 0),
        point_color: tuple[int, int, int] = (0, 0, 255),
        line_thickness: int = 2,
        point_radius: int = 4,
    ) -> None:
        """
        参数说明：
        - line_color:
            骨架连线颜色，BGR 格式
        - point_color:
            关键点颜色，BGR 格式
        - line_thickness:
            连线粗细
        - point_radius:
            关键点半径
        """
        self.line_color = line_color
        self.point_color = point_color
        self.line_thickness = line_thickness
        self.point_radius = point_radius

    def draw(self, frame, pose_landmarks: PoseLandmarks):
        """
        在输入图像上绘制骨架和关键点，并返回绘制后的图像。

        参数：
        - frame:
            OpenCV BGR 图像
        - pose_landmarks:
            当前帧关键点集合

        返回：
        - 绘制后的图像对象
        """
        image_height, image_width = frame.shape[:2]

        self._draw_connections(frame, pose_landmarks, image_width, image_height)
        self._draw_points(frame, pose_landmarks, image_width, image_height)

        return frame

    def _draw_connections(
        self,
        frame,
        pose_landmarks: PoseLandmarks,
        image_width: int,
        image_height: int,
    ) -> None:
        """
        绘制骨架连线。
        """
        for start_name, end_name in self.CONNECTIONS:
            start_landmark = pose_landmarks.get(start_name)
            end_landmark = pose_landmarks.get(end_name)

            if start_landmark is None or end_landmark is None:
                continue

            start_point = (
                int(start_landmark.x * image_width),
                int(start_landmark.y * image_height),
            )
            end_point = (
                int(end_landmark.x * image_width),
                int(end_landmark.y * image_height),
            )

            cv2.line(
                frame,
                start_point,
                end_point,
                self.line_color,
                self.line_thickness,
            )

    def _draw_points(
        self,
        frame,
        pose_landmarks: PoseLandmarks,
        image_width: int,
        image_height: int,
    ) -> None:
        """
        绘制关键点。
        """
        for point_name in self.POINT_NAMES:
            landmark = pose_landmarks.get(point_name)
            if landmark is None:
                continue

            point = (
                int(landmark.x * image_width),
                int(landmark.y * image_height),
            )

            cv2.circle(
                frame,
                point,
                self.point_radius,
                self.point_color,
                -1,
            )