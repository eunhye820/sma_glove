"""
실제 SMA 글러브에 연결해서 4채널 센서값을 읽고,
그 값으로 URDF 손 모델(pybullet GUI)을 실시간으로 갱신하는 예제.

사용 전 확인:
  1) sma_glove_4channel.ino 펌웨어가 업로드된 Mega가 PORT에 연결돼 있어야 함
  2) pip install -e . (또는 pip install -r requirements.txt) 로 의존성 설치
  3) 아래 PORT 값을 본인 환경에 맞게 수정
     - Windows: "COM5" 같은 형식
     - macOS:   "/dev/cu.usbmodemXXXX"
     - Linux:   "/dev/ttyACM0" 또는 "/dev/ttyUSB0"
     포트 이름을 모르면: python -m serial.tools.list_ports
"""

from sma_glove import Glove

PORT = "/dev/ttyACM0"


def main():
    with Glove(PORT, use_gui=True) as glove:
        print("연결됨. URDF 창에서 실시간 각도를 확인하세요. (Ctrl+C로 종료)")
        try:
            glove.run(hz=30)
        except KeyboardInterrupt:
            print("종료합니다.")


if __name__ == "__main__":
    main()
