# sma-glove

SMA 글러브(Arduino Mega 4채널 펌웨어)와 시리얼로 통신하면서,
동시에 URDF 손 모델을 pybullet으로 시각화하는 파이썬 패키지입니다.

```
센서값 읽기 (입력)   :  Arduino  --시리얼-->  Python  --> URDF 관절 갱신(시각화)
명령 보내기 (출력)   :  Python  --시리얼-->  Arduino (S<채널> <각도>)
```

## 설치

```bash
cd sma_glove_pkg
pip install -e .
# 또는
pip install -r requirements.txt
```

## 폴더 구조

```
sma_glove_pkg/
  sma_glove/
    serial_link.py   # 시리얼로 센서값 읽기 / 명령 전송
    model.py         # URDF 로드 + 관절 각도 갱신 (pybullet)
    glove.py         # 위 둘을 합친 상위 API (Glove 클래스)
    urdf/sma_hand.urdf  # 샘플 5손가락 URDF (joint 이름: finger1_joint ~ finger5_joint)
  examples/
    live_demo.py          # 실시간 센서값 -> 시각화
    send_command_demo.py  # 채널에 목표각도 전송 예제
```

## 빠른 사용법

```python
from sma_glove import Glove

with Glove(port="/dev/ttyACM0") as glove:
    glove.move(channel=0, angle_deg=45)   # 출력: 손가락1(채널0)을 45도로 구동
    state = glove.read()                  # 입력: 센서값 읽기 + URDF 시각화 갱신
    print(state["Finger1"].angle)
```

- `port`: 본인 환경의 시리얼 포트. 모르면 터미널에서
  ```bash
  python -m serial.tools.list_ports
  ```
- 채널 번호 ↔ 손가락 매핑 (펌웨어와 동일):

  | 채널 | 손가락 | URDF 조인트 |
  |---|---|---|
  | 0 | Finger1 | finger1_joint |
  | 1 | Finger2 | finger2_joint |
  | 2 | Finger3 | finger3_joint |
  | 3 | Finger4&5 | finger4_joint, finger5_joint (동시 구동) |

## 본인 URDF로 바꾸기

기본 제공 `sma_hand.urdf`는 손가락마다 1축 revolute 조인트만 있는 단순한 형태입니다.
실제 손 모델(메쉬 포함 등)을 쓰시려면:

```python
glove = Glove(port="/dev/ttyACM0", urdf_path="내손모델.urdf")
```

조인트 이름이 `finger1_joint` 같은 기본값과 다르면 매핑을 직접 넘겨주세요:

```python
glove = Glove(
    port="/dev/ttyACM0",
    urdf_path="내손모델.urdf",
    channel_to_joints={
        0: ["thumb_flex"],
        1: ["index_flex"],
        2: ["middle_flex"],
        3: ["ring_flex", "pinky_flex"],
    },
)
```

## SolidWorks/ROS에서 익스포트한 URDF 쓰기 (package:// 경로 문제)

SolidWorks URDF Exporter로 뽑은 파일은 메시 경로가
`<mesh filename="package://패키지명/meshes/xxx.STL"/>` 형태인데,
pybullet은 ROS 패키지 경로(`package://`)를 못 읽습니다.
또 조인트 `<limit lower="0" upper="0" .../>` 이 전부 0으로 export되는 경우가 많아
실제로는 안 움직이는 상태로 나옵니다.

`exoskeleton/hand_exoskeleton_fixed.urdf`는 이 두 가지를 미리 고쳐둔 예시 파일입니다
(메시 경로는 `meshes/xxx.STL` 형태로, limit은 임시로 ±180도로 넓혀둠 — 실제 기계적 한계에
맞게 다시 좁히는 걸 권장합니다).

실제 `.STL` 파일은 용량 문제로 포함하지 못했으니, 본인 ROS 워크스페이스의 `meshes/` 폴더를
이 컴퓨터의 아무 경로에 복사해두고 `meshes_dir`로 알려주면 됩니다. 패키지가 경로 형태와
상관없이 파일명만 보고 절대경로로 다시 연결해줍니다:

```python
from sma_glove import Glove, HAND_EXOSKELETON_CHANNEL_TO_JOINTS

glove = Glove(
    port="/dev/ttyACM0",
    urdf_path="exoskeleton/hand_exoskeleton_fixed.urdf",
    meshes_dir="/home/icrs/hand_ws/hand exoskeleton.SLDASM/meshes",  # 본인 경로
    channel_to_joints=HAND_EXOSKELETON_CHANNEL_TO_JOINTS,
)
```

`examples/exoskeleton_demo.py` 에 그대로 실행 가능한 예제가 있습니다.

`HAND_EXOSKELETON_CHANNEL_TO_JOINTS`는 손가락 번호를 1=엄지 ... 5=소지로 가정하고
각 손가락의 굽힘(x축) 조인트만 묶은 매핑입니다 (베이스 벌림용 z축 조인트는 제외).
실제 번호 순서가 다르면 `sma_glove/model.py`에서 직접 수정하세요.

## GUI 없이 쓰기 (헤드리스/서버 환경)

```python
glove = Glove(port="/dev/ttyACM0", use_gui=False)
```

## 참고

- 시리얼 라인 파싱은 이전에 만든 `sma_glove_4channel.ino` 펌웨어의 출력 형식
  (`... | Finger1 sp:.. ang:.. pwm:.. | ...`)에 맞춰져 있습니다.
  펌웨어의 디버그 출력 형식을 바꾸면 `sma_glove/serial_link.py`의 정규식도 같이 수정해야 합니다.

## 진행 상황 로그 (검지 채널 HW 이슈)

> 이 섹션은 작업하면서 계속 아래에 새 항목을 추가합니다(기존 항목은 지우지 않음).
> 최신 항목이 맨 아래에 오며, 이전과 달라진 점을 항목마다 명시합니다.

### 2026-09-18 — 문제 발견: PWM 배선 검지↔중지 스왑
- `Flex_angle_mapping_control_2ch.ino` 기준, 소프트웨어로 "중지"(channel2) 채널에 pwm2=255를 보냈는데 실제로는 검지가 가열됨 → 단일 채널 통제 테스트로 재현 확정.
- 원인 추정: ENA/IN1/IN2(액추에이터 구동 신호선)만 채널1↔채널2 사이에서 물리적으로 뒤바뀜. 센서(flex/IMU)는 정상 배선.
- 부작용: 채널 자체 안전로직(flex 도달 판정)이 무의미해져, 목표 도달을 감지 못하고 풀파워(255) 지속 위험.
- 아두이노 Mega가 세션 중 USB 재연결(`/dev/ttyACM0` 재생성)을 7회 이상 반복 — 원인 미해결(케이블/전원 브라운아웃 의심).

### 2026-09-23 — 코드상 수정 확인 (실기 검증 전)
- **달라진 점**: `Flex_angle_mapping_control_2ch.ino`를 다시 읽어본 결과, PWM 스왑이 펌웨어에서 이미 교차 매핑으로 수정되어 있음 확인.
  - `act1`(검지 제어루프)에 원래 채널2 출력핀(`ENA2_PIN/IN1_2_PIN/IN2_2_PIN`)을 배정
  - `act2`(중지 제어루프)에 원래 채널1 출력핀(`ENA1_PIN/IN1_1_PIN/IN2_1_PIN`)을 배정
  - 즉 물리적 재배선이 아니라 소프트웨어 핀 교차 배정으로 해결한 방식.
- **여전히 미확인**: 이 코드가 실제 아두이노 Mega에 재업로드됐는지, 재업로드 후 검지/중지가 각각 올바르게 구동되는지 실측 검증 안 됨.
- USB 재연결 반복 문제: 여전히 미해결 (코드 확인만으로는 안 풀리는 별개의 HW 이슈).

### 다음에 확인할 것 (아직 미해결 상태)
- [ ] 위 수정 코드가 실제 보드에 업로드돼 있는지 확인, 안 됐으면 재업로드.
- [ ] 업로드 후 단일 채널 통제 테스트로 검지=검지, 중지=중지 매핑 재검증 (이전 "검증 완료" 기록은 스왑 상태에서 나온 것일 수 있어 무효 취급).
- [ ] USB 케이블/전원 공급 육안 점검 및 교체.
- [ ] 위 두 가지 해결 후, flex1(검지) 간헐적 스파이크가 실제 크로스토크 문제인지 재검증.
- 안전 참고: 테스트 재개 시에도 5초 이내 짧게만 명령하고 즉시 estop/REST 복귀, 실시간 물리적 온도 확인.
