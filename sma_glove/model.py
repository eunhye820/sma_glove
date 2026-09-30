"""
URDF로 표현된 글러브(손) 모델을 불러오고, 센서값에 맞춰 관절 각도를 갱신하는 모듈.
시각화는 pybullet GUI를 사용합니다 (DIRECT 모드로 GUI 없이도 가능).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

import pybullet as p

from .urdf_tools import fix_urdf_mesh_paths

DEFAULT_URDF = str(Path(__file__).parent / "urdf" / "sma_hand.urdf")

# 채널(0~3) -> 실제로 움직여야 하는 URDF 조인트 이름들 (기본 제공 샘플 URDF용).
# 4번 채널(Finger4&5)은 손가락 4,5 두 조인트를 같이 구동합니다.
# 본인 URDF의 조인트 이름이 다르면 Glove/GloveModel 생성 시 channel_to_joints로 덮어쓰세요.
CHANNEL_TO_JOINTS: Dict[int, List[str]] = {
    0: ["finger1_joint"],
    1: ["finger2_joint"],
    2: ["finger3_joint"],
    3: ["finger4_joint", "finger5_joint"],
}

# hand_exoskeleton_SLDASM.urdf(SolidWorks 익스포트) 전용 매핑.
# 손가락 번호는 1=엄지 ... 5=소지 순서로 가정했습니다 (다르면 직접 수정하세요).
# 각 손가락의 "_1"(엄지는 "_1","_2") 조인트는 z축 기준 베이스 위치(벌림) 조인트라
# 굽힘 센서 1개로는 구동하지 않고 그대로 둡니다. 굽힘에 해당하는 x축 조인트들만 묶었습니다.
HAND_EXOSKELETON_CHANNEL_TO_JOINTS: Dict[int, List[str]] = {
    0: ["thumb_3", "thumb_4", "thumb_5"],                                # 손가락1 = 엄지
    1: ["index_2", "index_3", "index_4"],                                # 손가락2 = 인지
    2: ["middle_2", "middle_3", "middle_4"],                             # 손가락3 = 중지
    3: ["ring_2", "ring_3", "ring_4", "pinky_2", "pinky_3", "pinky_4"],  # 손가락4&5 = 약지+소지
}


class GloveModel:
    """pybullet으로 글러브 URDF를 불러와 관절 각도를 표시/갱신하는 클래스."""

    def __init__(
        self,
        urdf_path: Optional[str] = None,
        use_gui: bool = True,
        channel_to_joints: Optional[Dict[int, List[str]]] = None,
        meshes_dir: Optional[str] = None,
    ):
        urdf_path = str(urdf_path or DEFAULT_URDF)
        if meshes_dir is not None:
            # package:// 등 메시 경로를 meshes_dir 기준 절대경로로 고친 새 urdf를 만들어서 사용
            urdf_path = fix_urdf_mesh_paths(urdf_path, meshes_dir)
        self.urdf_path = urdf_path
        self.channel_to_joints = channel_to_joints or CHANNEL_TO_JOINTS

        self._client = p.connect(p.GUI if use_gui else p.DIRECT)
        p.setGravity(0, 0, 0)  # 센서값으로 직접 관절을 세팅하는 용도라 중력은 끔
        self.body_id = p.loadURDF(self.urdf_path, useFixedBase=True)
        self._joint_index = self._build_joint_index()

    def _build_joint_index(self) -> Dict[str, int]:
        index: Dict[str, int] = {}
        for i in range(p.getNumJoints(self.body_id)):
            info = p.getJointInfo(self.body_id, i)
            joint_name = info[1].decode()
            index[joint_name] = i
        return index

    @property
    def joint_names(self) -> List[str]:
        """URDF에서 실제로 인식된 조인트 이름 목록 (디버깅용)."""
        return list(self._joint_index.keys())

    def set_joint_angle(self, joint_name: str, angle_deg: float) -> None:
        if joint_name not in self._joint_index:
            raise KeyError(
                f"URDF에 '{joint_name}' 조인트가 없습니다. "
                f"사용 가능한 조인트: {self.joint_names}"
            )
        p.resetJointState(
            self.body_id, self._joint_index[joint_name], math.radians(angle_deg)
        )

    def set_channel_angle(self, channel: int, angle_deg: float) -> None:
        for joint_name in self.channel_to_joints.get(channel, []):
            self.set_joint_angle(joint_name, angle_deg)

    def update_from_sensor_state(self, state: Dict) -> None:
        """SerialLink.read_state()의 결과(dict)를 받아 4채널 각도를 한 번에 반영."""
        from .serial_link import CHANNEL_NAMES

        for channel, name in enumerate(CHANNEL_NAMES):
            if name in state:
                self.set_channel_angle(channel, state[name].angle)

    def step(self) -> None:
        p.stepSimulation()

    def close(self) -> None:
        p.disconnect(self._client)
