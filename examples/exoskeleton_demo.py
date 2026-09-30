"""
hand_exoskeleton_SLDASM.urdf (SolidWorks 익스포트)를 가지고 실시간 시각화하는 예제.

사용 전 준비:
  1) 원래 ROS 패키지의 `meshes/` 폴더(STL 파일들)를 이 컴퓨터 어딘가에 복사
     예) ~/hand_ws/hand exoskeleton.SLDASM/meshes/
  2) 아래 MESHES_DIR을 그 경로로 수정
  3) exoskeleton/hand_exoskeleton_fixed.urdf 는 이미
     - package:// 경로 -> meshes/xxx.STL 로 정리
     - 조인트 limit(0,0,0,0) placeholder -> 사용 가능한 값으로 수정
     해둔 파일입니다. meshes_dir만 알려주면 나머지 경로는 자동으로 절대경로로 바뀝니다.
"""

import time

from sma_glove import Glove, HAND_EXOSKELETON_CHANNEL_TO_JOINTS

PORT = "/dev/ttyACM0"
URDF_PATH = "exoskeleton/hand_exoskeleton_fixed.urdf"
MESHES_DIR = "/home/icrs/hand_ws/hand exoskeleton.SLDASM/meshes"  # 본인 경로로 수정


def main():
    with Glove(
        PORT,
        urdf_path=URDF_PATH,
        meshes_dir=MESHES_DIR,
        channel_to_joints=HAND_EXOSKELETON_CHANNEL_TO_JOINTS,
        use_gui=True,
    ) as glove:
        print("연결됨. 실제 외골격 메시가 보이는지 확인하세요. (Ctrl+C로 종료)")
        try:
            glove.run(hz=30)
        except KeyboardInterrupt:
            print("종료합니다.")


if __name__ == "__main__":
    main()
