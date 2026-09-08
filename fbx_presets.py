"""CAT Menus FBX 내보내기 프리셋 로컬 저장소.

프리셋은 Blender 사용자 설정 디렉터리(`CONFIG/cat_menus/fbx_presets.json`)에
JSON 형태로 저장되므로 블렌드 파일이나 애드온 재설치와 무관하게 유지된다.
저장되는 키 이름은 `bpy.ops.export_scene.fbx()` 인자 이름과 맞추고,
CAT 전용 항목(`export_subdir`)만 예외로 둔다.
"""

import json
import os

import bpy

# 프리셋 파일 위치
CONFIG_DIR_NAME = "cat_menus"
PRESET_FILE_NAME = "fbx_presets.json"

# 저장 파일 스키마 버전
STORE_VERSION = 1

# 프리셋 기본값. `+프리셋` 대화창의 초기값이자 저장값 보정 기준이 된다.
DEFAULT_PRESET = {
    "export_dir": "",                   # 고정 내보내기 폴더. 비우면 export_subdir을 사용한다
    "export_subdir": "FBX",             # .blend 파일 옆에 만들 내보내기 폴더 이름
    "object_types": ["MESH"],           # 내보낼 오브젝트 타입
    "use_mesh_modifiers": True,         # 모디파이어 적용 여부
    "mesh_smooth_type": "FACE",         # 스무딩 정보 방식
    "use_triangles": False,             # 삼각형 분할 여부
    "use_custom_props": False,          # 커스텀 프로퍼티 포함 여부
    "bake_anim": False,                 # 애니메이션 베이크 여부
    "global_scale": 1.0,                # 전역 스케일
    "apply_unit_scale": True,           # 유닛 스케일 적용 여부
    "apply_scale_options": "FBX_SCALE_NONE",  # 스케일 적용 방식
    "axis_forward": "-Z",               # 전방 축
    "axis_up": "Y",                     # 상방 축
    "path_mode": "AUTO",                # 텍스처 경로 처리 방식
}

# CAT 전용 키. `bpy.ops.export_scene.fbx()` 로 넘기지 않는다.
CAT_ONLY_KEYS = ("export_dir", "export_subdir")

# 열거형 항목 정의. 대화창과 저장값 검증에 함께 사용한다.
OBJECT_TYPE_ITEMS = (
    ('EMPTY', "Empty", "빈 오브젝트"),
    ('CAMERA', "Camera", "카메라"),
    ('LIGHT', "Light", "라이트"),
    ('ARMATURE', "Armature", "아마추어"),
    ('MESH', "Mesh", "메시"),
    ('OTHER', "Other", "커브, 서피스 등 기타 타입"),
)

MESH_SMOOTH_TYPE_ITEMS = (
    ('OFF', "Normals Only", "노멀만 내보냅니다"),
    ('FACE', "Face", "면 단위 스무딩 정보를 내보냅니다"),
    ('EDGE', "Edge", "엣지 단위 스무딩 정보를 내보냅니다"),
    ('CUSTOM_NORMALS', "Custom Normals", "커스텀 노멀을 내보냅니다"),
)

APPLY_SCALE_OPTIONS_ITEMS = (
    ('FBX_SCALE_NONE', "All Local", "모든 스케일을 로컬로 적용합니다"),
    ('FBX_SCALE_UNITS', "FBX Units Scale", "유닛 스케일만 FBX 스케일로 넘깁니다"),
    ('FBX_SCALE_CUSTOM', "FBX Custom Scale", "커스텀 스케일만 FBX 스케일로 넘깁니다"),
    ('FBX_SCALE_ALL', "FBX All", "모든 스케일을 FBX 스케일로 넘깁니다"),
)

AXIS_ITEMS = (
    ('X', "X", "X 축"),
    ('Y', "Y", "Y 축"),
    ('Z', "Z", "Z 축"),
    ('-X', "-X", "-X 축"),
    ('-Y', "-Y", "-Y 축"),
    ('-Z', "-Z", "-Z 축"),
)

PATH_MODE_ITEMS = (
    ('AUTO', "Auto", "상황에 맞게 자동 선택합니다"),
    ('ABSOLUTE', "Absolute", "절대 경로로 저장합니다"),
    ('RELATIVE', "Relative", "상대 경로로 저장합니다"),
    ('MATCH', "Match", "원본 경로 방식을 따릅니다"),
    ('STRIP', "Strip Path", "파일 이름만 남깁니다"),
    ('COPY', "Copy", "텍스처를 함께 복사합니다"),
)


def _identifiers(items):
    """열거형 항목 정의에서 식별자 집합을 만든다."""
    return {item[0] for item in items}


ENUM_VALUES = {
    "mesh_smooth_type": _identifiers(MESH_SMOOTH_TYPE_ITEMS),
    "apply_scale_options": _identifiers(APPLY_SCALE_OPTIONS_ITEMS),
    "axis_forward": _identifiers(AXIS_ITEMS),
    "axis_up": _identifiers(AXIS_ITEMS),
    "path_mode": _identifiers(PATH_MODE_ITEMS),
}

OBJECT_TYPE_VALUES = _identifiers(OBJECT_TYPE_ITEMS)


def preset_file_path():
    """프리셋 JSON 파일의 전체 경로를 돌려준다.

    Returns:
        프리셋 파일 경로. 설정 디렉터리를 확보하지 못하면 빈 문자열.
    """
    config_dir = bpy.utils.user_resource('CONFIG', path=CONFIG_DIR_NAME, create=True)
    if not config_dir:
        return ""
    return os.path.join(config_dir, PRESET_FILE_NAME)


def normalize_preset(raw):
    """저장값이나 입력값을 기본값 기준으로 보정한다.

    Args:
        raw: 보정할 프리셋 딕셔너리

    Returns:
        기본값의 모든 키를 갖추고 타입이 검증된 새 딕셔너리
    """
    preset = dict(DEFAULT_PRESET)
    if not isinstance(raw, dict):
        return preset

    for key, default in DEFAULT_PRESET.items():
        if key not in raw:
            continue
        value = raw[key]

        if key == "object_types":
            # 알 수 없는 타입은 버리고, 전부 비면 기본값으로 되돌린다.
            if isinstance(value, (list, tuple, set)):
                types = [item for item in value if item in OBJECT_TYPE_VALUES]
                preset[key] = sorted(types) if types else list(default)
            continue

        if key in ENUM_VALUES:
            if value in ENUM_VALUES[key]:
                preset[key] = value
            continue

        if isinstance(default, bool):
            preset[key] = bool(value)
        elif isinstance(default, float):
            try:
                preset[key] = float(value)
            except (TypeError, ValueError):
                pass
        elif isinstance(default, str):
            if isinstance(value, str):
                preset[key] = value

    # 내보내기 폴더 이름은 경로 구분자와 공백을 제거해 안전하게 만든다.
    preset["export_subdir"] = sanitize_subdir(preset["export_subdir"])
    preset["export_dir"] = (preset["export_dir"] or "").strip()
    return preset


def sanitize_subdir(name):
    """내보내기 하위 폴더 이름에서 위험한 문자를 제거한다.

    Args:
        name: 사용자가 입력한 폴더 이름

    Returns:
        경로 탈출과 잘못된 문자를 제거한 폴더 이름. 비면 기본값.
    """
    cleaned = (name or "").strip().strip("/\\")
    for bad in '<>:"|?*':
        cleaned = cleaned.replace(bad, "_")
    # 상위 경로 이동을 막는다.
    parts = [part for part in cleaned.replace("\\", "/").split("/") if part not in ("", ".", "..")]
    return "/".join(parts) or DEFAULT_PRESET["export_subdir"]


def resolve_export_dir(preset, blend_filepath):
    """프리셋 설정으로 실제 내보내기 폴더 경로를 계산한다.

    `export_dir`이 지정되어 있으면 그 폴더를 그대로 쓰고, 비어 있으면
    블렌드 파일이 있는 폴더 아래에 `export_subdir` 폴더를 쓴다.

    Args:
        preset: 설정 딕셔너리
        blend_filepath: 현재 블렌드 파일 경로. 저장 전이면 빈 문자열

    Returns:
        `(폴더 경로, 오류 메시지)` 튜플. 경로를 정할 수 없으면 경로가 빈 문자열이다.
    """
    settings = normalize_preset(preset)
    target = settings["export_dir"]

    if target:
        # `//` 접두사(블렌드 파일 기준 상대 경로)를 절대 경로로 바꾼다.
        if target.startswith("//") and not blend_filepath:
            return "", "이 프리셋의 내보내기 폴더는 블렌드 파일 기준 상대 경로이므로 파일을 먼저 저장해야 합니다."

        resolved = os.path.normpath(bpy.path.abspath(target))
        if not os.path.isabs(resolved):
            # 사용자가 상대 경로를 직접 입력한 경우 블렌드 파일 폴더를 기준으로 삼는다.
            if not blend_filepath:
                return "", "이 프리셋의 내보내기 폴더가 상대 경로이므로 블렌드 파일을 먼저 저장해야 합니다."
            resolved = os.path.normpath(os.path.join(os.path.dirname(blend_filepath), resolved))
        return resolved, ""

    if not blend_filepath:
        return "", "블렌드 파일을 먼저 저장하거나 프리셋에 내보내기 폴더를 지정하세요."

    subdir_parts = settings["export_subdir"].split("/")
    return os.path.normpath(os.path.join(os.path.dirname(blend_filepath), *subdir_parts)), ""


def load_presets():
    """저장된 프리셋 전체를 읽는다.

    Returns:
        `{프리셋 이름: 설정 딕셔너리}` 형태의 딕셔너리. 파일이 없거나 손상되면 빈 딕셔너리.
    """
    path = preset_file_path()
    if not path or not os.path.isfile(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError) as error:
        print(f"[CAT Menus] FBX 프리셋을 읽지 못했습니다: {error}")
        return {}

    presets = data.get("presets") if isinstance(data, dict) else None
    if not isinstance(presets, dict):
        return {}

    return {
        str(name): normalize_preset(settings)
        for name, settings in presets.items()
        if str(name).strip()
    }


def save_presets(presets):
    """프리셋 전체를 파일에 저장한다.

    Args:
        presets: `{프리셋 이름: 설정 딕셔너리}` 형태의 딕셔너리

    Returns:
        저장한 파일 경로. 실패하면 빈 문자열.
    """
    path = preset_file_path()
    if not path:
        print("[CAT Menus] Blender 설정 디렉터리를 확보하지 못해 프리셋을 저장할 수 없습니다.")
        return ""

    payload = {
        "version": STORE_VERSION,
        "presets": {name: presets[name] for name in sorted(presets)},
    }

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
    except OSError as error:
        print(f"[CAT Menus] FBX 프리셋을 저장하지 못했습니다: {error}")
        return ""

    return path


def preset_names():
    """메뉴 표시용 프리셋 이름 목록을 이름순으로 돌려준다."""
    return sorted(load_presets())


def get_preset(name):
    """이름으로 프리셋 하나를 찾는다.

    Args:
        name: 프리셋 이름

    Returns:
        설정 딕셔너리. 없으면 None.
    """
    return load_presets().get(name)


def add_preset(name, settings):
    """프리셋을 추가하거나 같은 이름의 프리셋을 덮어쓴다.

    Args:
        name: 프리셋 이름
        settings: 저장할 설정 딕셔너리

    Returns:
        `(성공 여부, 덮어썼는지 여부)` 튜플
    """
    key = (name or "").strip()
    if not key:
        return False, False

    presets = load_presets()
    replaced = key in presets
    presets[key] = normalize_preset(settings)
    return bool(save_presets(presets)), replaced


def remove_preset(name):
    """프리셋을 삭제한다.

    Args:
        name: 프리셋 이름

    Returns:
        삭제 성공 여부
    """
    presets = load_presets()
    if name not in presets:
        return False

    del presets[name]
    return bool(save_presets(presets))


def export_kwargs(preset):
    """프리셋을 `bpy.ops.export_scene.fbx()` 인자로 변환한다.

    Args:
        preset: 설정 딕셔너리

    Returns:
        연산자에 그대로 넘길 수 있는 키워드 인자 딕셔너리
    """
    kwargs = {
        key: value
        for key, value in normalize_preset(preset).items()
        if key not in CAT_ONLY_KEYS
    }
    kwargs["object_types"] = set(kwargs["object_types"])
    return kwargs
