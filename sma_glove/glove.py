"""
SerialLink(하드웨어 통신)와 GloveModel(URDF 시각화)을 하나로 묶은 상위 API.

기본적인 사용 흐름:

    from sma_glove import Glove

    with Glove(port="/dev/ttyACM0") as glove:
        glove.move(channel=0, angle_deg=45)   # 손가락1을 45도로 (출력 = 하드웨어 명령)
        state = glove.read()                  # 4채널 센서값 읽기 + 시각화 갱신 (입력)
        print(state["Finger1"].angle)
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from .model import CHANNEL_TO_JOINTS, GloveModel
from .serial_link import ChannelState, SerialLink


class Glove:
    """실제 SMA 글러브(시리얼) + URDF 시각화를 동시에 다루는 클래스."""

    def __init__(
        self,
        port: str,
        urdf_path: Optional[str] = None,
        baudrate: int = 115200,
        use_gui: bool = True,
        channel_to_joints: Optional[Dict[int, List[str]]] = None,
        meshes_dir: Optional[str] = None,
    ):
        self.link = SerialLink(port, baudrate=baudrate)
        self.model = GloveModel(
            urdf_path=urdf_path,
            use_gui=use_gui,
            channel_to_joints=channel_to_joints or CHANNEL_TO_JOINTS,
            meshes_dir=meshes_dir,
        )
        self._last_state: Dict[str, ChannelState] = {}

    def connect(self) -> "Glove":
        self.link.connect()
        return self

    def __enter__(self) -> "Glove":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ---------------- 입력 (센서값) ----------------
    def read(self) -> Dict[str, ChannelState]:
        """하드웨어에서 한 줄을 읽어 내부 상태 갱신 + 시각화 갱신 후 최신 상태 반환."""
        new_state = self.link.read_state()
        if new_state:
            self._last_state.update(new_state)
            self.model.update_from_sensor_state(new_state)
        self.model.step()
        return self._last_state

    # ---------------- 출력 (명령) ----------------
    def move(self, channel: int, angle_deg: float) -> None:
        """채널에 목표각도를 전송해서 실제 SMA 와이어를 구동."""
        self.link.send_setpoint(channel, angle_deg)

    # ---------------- 편의 기능 ----------------
    def run(self, hz: float = 30.0, duration: Optional[float] = None) -> None:
        """주기적으로 read()를 호출해 시각화를 계속 갱신 (블로킹)."""
        period = 1.0 / hz
        start = time.time()
        while duration is None or (time.time() - start) < duration:
            self.read()
            time.sleep(period)

    def close(self) -> None:
        self.link.close()
        self.model.close()
