"""
특정 채널(손가락)에 목표각도를 보내고, 실제로 그 각도에 도달하는 과정을
센서값으로 확인하는 예제.
"""

import time

from sma_glove import Glove

PORT = "/dev/ttyACM0"


def main():
    with Glove(PORT, use_gui=True) as glove:
        glove.move(channel=0, angle_deg=45)  # 손가락1(채널0)을 45도로 구동
        print("채널0 목표각도 45도 전송. 5초간 각도 변화를 출력합니다.")

        start = time.time()
        while time.time() - start < 5.0:
            state = glove.read()
            if "Finger1" in state:
                f1 = state["Finger1"]
                print(f"sp={f1.setpoint:.1f}  ang={f1.angle:.1f}  pwm={f1.pwm}")
            time.sleep(0.05)


if __name__ == "__main__":
    main()
