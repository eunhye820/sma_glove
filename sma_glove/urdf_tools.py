"""
ROS 스타일(`package://...`)이나 상대경로로 된 <mesh filename="..."> 를
실제 meshes 폴더 위치에 맞춰 절대경로로 바꿔주는 유틸리티.

SolidWorks/Fusion의 URDF Exporter는 보통 메시 경로를
`package://<패키지명>/meshes/xxx.STL` 형태로 적어두는데,
pybullet은 ROS 노드가 아니라서 이 package:// 스킴을 못 읽습니다.
이 모듈은 경로 형태와 상관없이 파일명만 뽑아서 사용자가 알려준
meshes 폴더 기준 절대경로로 다시 이어붙입니다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

_MESH_FILENAME_RE = re.compile(r'filename="([^"]+)"')


def fix_urdf_mesh_paths(
    urdf_path: str,
    meshes_dir: str,
    output_path: Optional[str] = None,
) -> str:
    """urdf_path 안의 모든 메시 경로를 meshes_dir 기준 절대경로로 바꿔서 저장.

    Args:
        urdf_path: 원본(또는 한 번 손본) .urdf 파일 경로
        meshes_dir: 실제 .STL/.dae 파일들이 들어있는 폴더 경로
        output_path: 결과를 저장할 경로. 생략하면 "<원본이름>_resolved.urdf"

    Returns:
        결과로 생성된 .urdf 파일의 경로 (문자열)
    """
    src = Path(urdf_path)
    meshes_dir_resolved = Path(meshes_dir).expanduser().resolve()
    text = src.read_text(encoding="utf-8")

    def _replace(match: "re.Match[str]") -> str:
        original = match.group(1)
        filename = original.rsplit("/", 1)[-1]  # package://.../meshes/x.STL -> x.STL
        new_path = (meshes_dir_resolved / filename).as_posix()
        return f'filename="{new_path}"'

    fixed_text = _MESH_FILENAME_RE.sub(_replace, text)

    dst = Path(output_path) if output_path else src.with_name(src.stem + "_resolved.urdf")
    dst.write_text(fixed_text, encoding="utf-8")
    return str(dst)
