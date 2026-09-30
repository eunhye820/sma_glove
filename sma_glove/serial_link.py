"""
SMA 글러브 펌웨어(아두이노)와의 시리얼 통신 담당.

펌웨어가 매 루프마다 아래와 같은 한 줄을 출력한다고 가정합니다.

    12345 | Finger1 sp:30.0 ang:25.3 pwm:120 | Finger2 sp:30.0 ang:10.1 pwm:0 | ...

그리고 "S<채널 0~3> <목표각도>" 형식의 명령을 받아 setpoint를 갱신합니다.
(이전에 만든 sma_glove_4channel.ino 펌웨어와 1:1로 맞춰져 있습니다.)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Dict, Optional

import serial

# 펌웨어가 출력하는 4채널 이름 (채널 인덱스 0~3과 1:1 대응)
CHANNEL_NAMES = ["Finger1", "Finger2", "Finger3", "Finger4&5"]

_LINE_RE = re.compile(
    r"(?P<name>[\w&]+)\s+sp:(?P<sp>-?\d+\.?\d*)\s+"
    r"ang:(?P<ang>-?\d+\.?\d*)\s+pwm:(?P<pwm>-?\d+)"
)


@dataclass
class ChannelState:
    """한 채널(손가락)의 한 시점 상태."""
    name: str
    setpoint: float
    angle: float
    pwm: int


class SerialLink:
    """SMA 글러브 펌웨어와 시리얼로 데이터를 주고받는 클래스."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None

    # ---------------- 연결 관리 ----------------
    def connect(self) -> "SerialLink":
        self._ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(2.0)  # 아두이노 리셋 + IMU 캘리브레이션 대기 시간
        return self

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()

    def __enter__(self) -> "SerialLink":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _require_open(self) -> serial.Serial:
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("연결되어 있지 않습니다. connect()를 먼저 호출하세요.")
        return self._ser

    # ---------------- 입력 (센서값 읽기) ----------------
    def read_state(self) -> Dict[str, ChannelState]:
        """한 줄을 읽어서 그 줄에 들어있는 채널들의 상태를 dict로 반환합니다.
        새로 들어온 줄이 없거나 형식이 안 맞으면 빈 dict를 반환합니다."""
        ser = self._require_open()
        raw = ser.readline().decode(errors="ignore").strip()
        if not raw:
            return {}

        state: Dict[str, ChannelState] = {}
        for m in _LINE_RE.finditer(raw):
            name = m.group("name")
            state[name] = ChannelState(
                name=name,
                setpoint=float(m.group("sp")),
                angle=float(m.group("ang")),
                pwm=int(m.group("pwm")),
            )
        return state

    def read_all_available(self) -> Dict[str, ChannelState]:
        """버퍼에 쌓여있는 줄을 전부 소비하고 가장 최근 상태만 반환 (지연 줄이기용)."""
        latest: Dict[str, ChannelState] = {}
        ser = self._require_open()
        while ser.in_waiting:
            new_state = self.read_state()
            if new_state:
                latest.update(new_state)
        return latest

    # ---------------- 출력 (명령 전송) ----------------
    def send_setpoint(self, channel: int, angle_deg: float) -> None:
        """채널(0~3)에 목표각도를 전송. 펌웨어의 'S<채널> <각도>' 명령과 동일한 형식."""
        if not 0 <= channel < len(CHANNEL_NAMES):
            raise ValueError(f"채널은 0~{len(CHANNEL_NAMES) - 1} 사이여야 합니다.")
        ser = self._require_open()
        ser.write(f"S{channel} {angle_deg}\n".encode())
