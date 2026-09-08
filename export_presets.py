"""CAT Menus 내보내기 프리셋 저장소.

FBX/OBJ 프리셋을 Blender 사용자 설정 디렉터리
(`CONFIG/cat_menus/export_presets.json`)에 JSON으로 저장하므로 블렌드 파일이나
애드온 재설치와 무관하게 유지된다.

대화창에 표시할 옵션 목록·라벨·설명·기본값·범위는 실행 중인 Blender의 내보내기
연산자 RNA(`export_scene.fbx`, `wm.obj_export`)에서 직접 복제한다. 옵션을 이 파일에
따로 적어두지 않기 때문에 프리셋 설정이 Blender 기본 내보내기 설정과 항상 같은
항목·같은 영문 라벨을 갖고, Blender 버전이 올라가 옵션이 바뀌어도 그대로 따라간다.

저장 키는 연산자 인자 이름과 1:1로 맞추고, CAT 전용 항목만 예외로 둔다.
"""

import json
import math
import os

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

# 프리셋 파일 위치
CONFIG_DIR_NAME = "cat_menus"
PRESET_FILE_NAME = "export_presets.json"

# v0.1.3~v0.1.4에서 쓰던 FBX 전용 저장 파일. 처음 읽을 때 통합 저장소로 옮긴다.
LEGACY_FBX_FILE_NAME = "fbx_presets.json"

# 저장 파일 스키마 버전
STORE_VERSION = 2

# CAT 전용 키. 내보내기 연산자에는 넘기지 않는다.
EXPORT_DIR_KEY = "export_dir"
EXPORT_MODE_KEY = "export_mode"
CAT_ONLY_KEYS = (EXPORT_DIR_KEY, EXPORT_MODE_KEY)

# 선택한 오브젝트를 파일로 나누는 방식. Blender 내보내기에는 없는 CAT 전용 항목이다.
EXPORT_MODE_ITEMS = (
    ('PER_OBJECT', "Per Object",
     "Write one file per selected object, named after the object"),
    ('SINGLE', "Single File",
     "Write all selected objects into a single file named after the active object. "
     "Required when an armature and its meshes must stay in one file, such as animation exports"),
)
DEFAULT_EXPORT_MODE = 'PER_OBJECT'
_EXPORT_MODE_VALUES = {item[0] for item in EXPORT_MODE_ITEMS}

# 대화창으로 복제할 수 있는 RNA 프로퍼티 타입
_SUPPORTED_TYPES = frozenset({'BOOLEAN', 'ENUM', 'FLOAT', 'INT', 'STRING'})

# StringProperty가 받아들이는 subtype만 통과시킨다.
_STRING_SUBTYPES = frozenset({'NONE', 'FILE_PATH', 'DIR_PATH', 'FILE_NAME', 'BYTE_STRING', 'PASSWORD'})


# ---------------------------------------------------------------------------
# 저장소
# ---------------------------------------------------------------------------

def _config_path(file_name):
    """설정 디렉터리 안의 파일 경로를 만든다. 디렉터리를 못 얻으면 빈 문자열."""
    config_dir = bpy.utils.user_resource('CONFIG', path=CONFIG_DIR_NAME, create=True)
    if not config_dir:
        return ""
    return os.path.join(config_dir, file_name)


def preset_file_path():
    """프리셋 JSON 파일의 전체 경로를 돌려준다."""
    return _config_path(PRESET_FILE_NAME)


def _read_json(path):
    """JSON 파일을 읽는다. 없거나 손상되면 None."""
    if not path or not os.path.isfile(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError) as error:
        print(f"[CAT Menus] 프리셋을 읽지 못했습니다: {path}: {error}")
        return None


def _clean_section(raw):
    """`{프리셋 이름: 설정}` 형태만 남긴다."""
    if not isinstance(raw, dict):
        return {}
    return {
        str(name): dict(settings)
        for name, settings in raw.items()
        if str(name).strip() and isinstance(settings, dict)
    }


def _read_legacy_fbx():
    """FBX 전용 저장 파일을 통합 저장소 형식으로 읽는다."""
    data = _read_json(_config_path(LEGACY_FBX_FILE_NAME))
    if not isinstance(data, dict):
        return {}
    return _clean_section(data.get("presets"))


def _read_store():
    """저장 파일 전체를 `{내보내기 키: {프리셋 이름: 설정}}` 형태로 읽는다.

    값은 보정하지 않고 저장된 그대로 둔다. 다른 Blender 버전에서 저장한 옵션이
    있어도 다시 저장할 때 사라지지 않도록 하기 위해서다.
    """
    data = _read_json(preset_file_path())

    store = {}
    if isinstance(data, dict):
        for key, section in data.items():
            if key == "version":
                continue
            cleaned = _clean_section(section)
            if cleaned:
                store[key] = cleaned

    if FBX_KEY not in store:
        legacy = _read_legacy_fbx()
        if legacy:
            store[FBX_KEY] = legacy

    return store


def _write_store(store):
    """저장소 전체를 파일에 쓴다."""
    path = preset_file_path()
    if not path:
        print("[CAT Menus] Blender 설정 디렉터리를 확보하지 못해 프리셋을 저장할 수 없습니다.")
        return False

    payload = {"version": STORE_VERSION}
    for key in sorted(store):
        payload[key] = {name: store[key][name] for name in sorted(store[key])}

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
    except OSError as error:
        print(f"[CAT Menus] 프리셋을 저장하지 못했습니다: {error}")
        return False

    return True


def load_presets(key):
    """내보내기 종류 하나의 프리셋 전체를 읽는다."""
    return _read_store().get(key, {})


def preset_names(key):
    """메뉴 표시용 프리셋 이름 목록을 이름순으로 돌려준다."""
    return sorted(load_presets(key))


def get_preset(key, name):
    """이름으로 프리셋 하나를 찾는다. 없으면 None."""
    return load_presets(key).get(name)


def add_preset(key, name, settings):
    """프리셋을 추가하거나 같은 이름의 프리셋을 덮어쓴다.

    Returns:
        `(성공 여부, 덮어썼는지 여부)` 튜플
    """
    preset_name = (name or "").strip()
    if not preset_name:
        return False, False

    store = _read_store()
    section = store.setdefault(key, {})
    replaced = preset_name in section
    section[preset_name] = dict(settings)
    return _write_store(store), replaced


def remove_preset(key, name):
    """프리셋을 삭제한다."""
    store = _read_store()
    section = store.get(key, {})
    if name not in section:
        return False

    del section[name]
    return _write_store(store)


def resolve_export_dir(preset, blend_filepath):
    """프리셋 설정으로 실제 내보내기 폴더 경로를 계산한다.

    `export_dir`이 지정되어 있으면 그 폴더로 바로 내보내고, 비어 있으면 블렌드
    파일이 있는 폴더에 바로 내보낸다. 하위 폴더를 따로 만들지 않는다.

    Returns:
        `(폴더 경로, 오류 메시지)` 튜플. 경로를 정할 수 없으면 경로가 빈 문자열이다.
    """
    target = ""
    if isinstance(preset, dict):
        value = preset.get(EXPORT_DIR_KEY, "")
        target = value.strip() if isinstance(value, str) else ""

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

    return os.path.normpath(os.path.dirname(blend_filepath)), ""


# ---------------------------------------------------------------------------
# 내보내기 연산자 RNA 복제
# ---------------------------------------------------------------------------

# 내보내기 연산자를 제공하는 애드온. OBJ 내보내기는 Blender에 내장되어 있어 없다.
_OPERATOR_ADDONS = {
    "export_scene.fbx": ("io_scene_fbx", "bl_ext.blender_org.io_scene_fbx"),
}


def _ensure_operator_addon(op_path):
    """내보내기 연산자를 제공하는 애드온을 먼저 등록시킨다.

    애드온 로드 순서에 따라 CAT Menus가 FBX 내보내기 애드온보다 먼저 켜질 수 있는데,
    그 상태에서는 옵션 정의를 읽을 수 없다. 사용자가 이미 켜 둔 애드온만 앞당겨
    등록하므로 일부러 꺼 둔 애드온을 되살리지는 않는다.

    Returns:
        등록을 시도했으면 True
    """
    try:
        import addon_utils

        enabled_addons = bpy.context.preferences.addons
        for module_name in _OPERATOR_ADDONS.get(op_path, ()):
            if module_name not in enabled_addons:
                continue
            if addon_utils.enable(module_name, default_set=False, persistent=True) is not None:
                return True
    except Exception as error:
        print(f"[CAT Menus] 내보내기 애드온을 먼저 등록하지 못했습니다: {op_path}: {error}")

    return False


def _read_operator_properties(op_path):
    """`모듈.연산자` 경로로 내보내기 연산자의 RNA 프로퍼티를 읽는다. 실패하면 빈 딕셔너리."""
    module_name, op_name = op_path.split(".", 1)
    module = getattr(bpy.ops, module_name, None)
    operator = getattr(module, op_name, None) if module is not None else None
    if operator is None:
        return {}

    try:
        rna = operator.get_rna_type()
    except Exception:
        # 해당 내보내기 애드온이 아직 등록되지 않았거나 꺼져 있으면 여기서 걸린다.
        return {}

    return {prop.identifier: prop for prop in rna.properties if prop.identifier != "rna_type"}




def _finite(value):
    """무한대·NaN 경계값은 버린다. bpy.props에 그대로 넘기면 안 되기 때문이다."""
    if isinstance(value, (int, float)) and math.isfinite(value):
        return value
    return None


def _rna_default(prop):
    """RNA 프로퍼티 기본값을 JSON으로 저장할 수 있는 값으로 바꾼다."""
    if prop.type == 'ENUM':
        return sorted(prop.default_flag) if prop.is_enum_flag else prop.default
    if prop.type == 'BOOLEAN':
        return bool(prop.default)
    if prop.type == 'INT':
        return int(prop.default)
    if prop.type == 'FLOAT':
        return float(prop.default)
    return str(prop.default)


def _coerce(prop, value):
    """저장값을 RNA 프로퍼티 타입에 맞게 바꾼다. 맞출 수 없으면 None."""
    if prop.type == 'ENUM':
        valid = {item.identifier for item in prop.enum_items}
        if prop.is_enum_flag:
            if not isinstance(value, (list, tuple, set)):
                return None
            picked = sorted({item for item in value if item in valid})
            return picked or None
        return value if value in valid else None

    if prop.type == 'BOOLEAN':
        return bool(value) if isinstance(value, (bool, int)) else None

    if prop.type == 'INT':
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    if prop.type == 'FLOAT':
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    if prop.type == 'STRING':
        return value if isinstance(value, str) else None

    return None


def _build_property(prop):
    """RNA 프로퍼티를 대화창에서 쓸 bpy 프로퍼티로 복제한다."""
    common = {"name": prop.name, "description": prop.description}

    if prop.type == 'BOOLEAN':
        return BoolProperty(default=bool(prop.default), **common)

    if prop.type == 'ENUM':
        items = tuple(
            (item.identifier, item.name, item.description)
            for item in prop.enum_items
        )
        if not items:
            return None
        if prop.is_enum_flag:
            return EnumProperty(
                items=items,
                default=set(prop.default_flag),
                options={'ENUM_FLAG'},
                **common,
            )
        return EnumProperty(items=items, default=prop.default, **common)

    if prop.type in {'FLOAT', 'INT'}:
        maker = FloatProperty if prop.type == 'FLOAT' else IntProperty
        kwargs = dict(common, default=_rna_default(prop))
        for source, target in (
            ("hard_min", "min"),
            ("hard_max", "max"),
            ("soft_min", "soft_min"),
            ("soft_max", "soft_max"),
        ):
            bound = _finite(getattr(prop, source, None))
            if bound is not None:
                kwargs[target] = bound
        # RNA는 float step을 실수로 돌려주지만 bpy.props는 정수(100 = 1.0)를 받는다.
        step = _finite(getattr(prop, "step", None))
        if step:
            kwargs["step"] = int(step)
        if prop.type == 'FLOAT':
            kwargs["precision"] = int(getattr(prop, "precision", 3))
        return maker(**kwargs)

    if prop.type == 'STRING':
        subtype = prop.subtype if prop.subtype in _STRING_SUBTYPES else 'NONE'
        return StringProperty(default=str(prop.default), subtype=subtype, **common)

    return None


class PanelDef:
    """대화창 패널 하나. Blender 내보내기 패널 구성을 그대로 옮긴 것이다."""

    def __init__(self, title, default_closed, toggle, props):
        self.title = title                    # None이면 패널 없이 최상단에 그린다
        self.default_closed = default_closed
        self.toggle = toggle                  # 패널 헤더에 체크박스로 놓을 프로퍼티
        self.props = props


class ExporterSpec:
    """내보내기 연산자 하나에 대한 프리셋 정의."""

    def __init__(self, key, op_path, extension, panels, forced_kwargs, skip_props):
        self.key = key
        self.op_path = op_path
        self.extension = extension
        self.panels = panels
        self.forced_kwargs = dict(forced_kwargs)
        self.skip_props = frozenset(skip_props)
        self._addon_attempted = False
        self._reported = False

    def invalidate(self):
        """실패 기록을 지운다. 애드온을 다시 등록할 때 호출한다."""
        self._addon_attempted = False
        self._reported = False

    def rna_properties(self):
        """내보내기 연산자의 RNA 프로퍼티를 `{이름: 프로퍼티}`로 돌려준다.

        RNA 참조는 내보내기 애드온이 다시 등록되면 무효가 되므로 캐시하지 않고
        호출할 때마다 새로 읽는다.
        """
        properties = _read_operator_properties(self.op_path)
        if properties:
            self._reported = False
            return properties

        if not self._addon_attempted:
            self._addon_attempted = True
            if _ensure_operator_addon(self.op_path):
                properties = _read_operator_properties(self.op_path)
                if properties:
                    self._reported = False
                    return properties

        if not self._reported:
            self._reported = True
            print(f"[CAT Menus] 내보내기 연산자 정보를 읽지 못했습니다: {self.op_path}")
        return {}

    def is_available(self):
        """내보내기 연산자를 쓸 수 있는지 확인한다."""
        return bool(self.rna_properties())

    def _is_exposable(self, prop):
        """프리셋으로 저장할 수 있는 옵션인지 판단한다."""
        if prop.identifier in self.skip_props or prop.identifier in self.forced_kwargs:
            return False
        if prop.is_hidden or prop.is_readonly:
            return False
        if prop.type not in _SUPPORTED_TYPES:
            return False
        if getattr(prop, "array_length", 0):
            return False
        return True

    def layout_groups(self):
        """`(패널 정의, 프로퍼티 이름 목록)` 목록을 그리는 순서대로 돌려준다."""
        available = self.rna_properties()
        groups = []
        seen = set()

        for panel in self.panels:
            picked = [
                name for name in panel.props
                if name in available and name not in seen and self._is_exposable(available[name])
            ]
            has_toggle = (
                panel.toggle in available
                and panel.toggle not in seen
                and self._is_exposable(available[panel.toggle])
            )
            if not picked and not has_toggle:
                continue
            seen.update(picked)
            if has_toggle:
                seen.add(panel.toggle)
            groups.append((panel if has_toggle else PanelDef(panel.title, panel.default_closed, None, ()), picked))

        # 패널 정의에 없는 옵션도 빠뜨리지 않는다. Blender 버전이 올라가며 옵션이
        # 늘어나도 프리셋에서 계속 다룰 수 있게 하기 위해서다.
        extra = [
            name for name, prop in available.items()
            if name not in seen and self._is_exposable(prop)
        ]
        if extra:
            groups.append((PanelDef("Other", True, None, ()), extra))

        return groups

    def option_names(self):
        """프리셋으로 저장할 옵션 이름을 그리는 순서대로 돌려준다."""
        names = []
        for panel, props in self.layout_groups():
            if panel.toggle:
                names.append(panel.toggle)
            names.extend(props)
        return names

    def defaults(self):
        """Blender 기본 내보내기 설정과 같은 기본 프리셋을 만든다."""
        preset = {
            EXPORT_DIR_KEY: "",
            EXPORT_MODE_KEY: DEFAULT_EXPORT_MODE,
        }
        properties = self.rna_properties()
        for name in self.option_names():
            preset[name] = _rna_default(properties[name])
        return preset

    def normalize(self, raw):
        """저장값을 현재 Blender가 이해할 수 있는 값으로 보정한다.

        이 Blender 버전에 없는 옵션이나 사라진 열거형 값은 기본값으로 되돌린다.
        """
        preset = self.defaults()
        if not isinstance(raw, dict):
            return preset

        properties = self.rna_properties()
        for key, value in raw.items():
            if key == EXPORT_DIR_KEY:
                preset[key] = value.strip() if isinstance(value, str) else ""
                continue
            if key == EXPORT_MODE_KEY:
                if value in _EXPORT_MODE_VALUES:
                    preset[key] = value
                continue
            if key not in preset:
                continue
            coerced = _coerce(properties[key], value)
            if coerced is not None:
                preset[key] = coerced

        return preset

    def export_kwargs(self, preset):
        """프리셋을 내보내기 연산자 키워드 인자로 바꾼다."""
        settings = self.normalize(preset)
        properties = self.rna_properties()

        kwargs = {}
        for name in self.option_names():
            prop = properties[name]
            value = settings[name]
            kwargs[name] = set(value) if prop.type == 'ENUM' and prop.is_enum_flag else value

        kwargs.update(self.forced_kwargs)
        return kwargs


def _is_enum_flag(prop):
    """열거형 다중 선택 여부. 열거형이 아니면 False."""
    return prop.type == 'ENUM' and prop.is_enum_flag


def collect_settings(spec, operator):
    """대화창 연산자에 입력된 값을 저장용 딕셔너리로 모은다."""
    settings = {
        EXPORT_DIR_KEY: operator.export_dir,
        EXPORT_MODE_KEY: operator.export_mode,
    }
    properties = spec.rna_properties()
    for name in spec.option_names():
        value = getattr(operator, name)
        settings[name] = sorted(value) if _is_enum_flag(properties[name]) else value
    return settings


def apply_dialog_properties(cls, spec):
    """프리셋 등록 대화창 클래스에 내보내기 옵션 프로퍼티를 붙인다.

    실행 중인 Blender의 내보내기 연산자에서 정의를 그대로 복제하므로 대화창이
    Blender 기본 내보내기 설정과 같은 항목·라벨·기본값을 갖는다.
    등록(`register`) 전에 호출해야 한다.
    """
    spec.invalidate()

    # 클래스에 직접 적어 둔 CAT 전용 프로퍼티는 매번 그대로 복원한다.
    static = cls.__dict__.get("_cat_static_annotations")
    if static is None:
        static = dict(cls.__dict__.get("__annotations__", {}))
        cls._cat_static_annotations = static

    annotations = dict(static)
    properties = spec.rna_properties()
    for name in spec.option_names():
        built = _build_property(properties[name])
        if built is not None:
            annotations[name] = built

    cls.__annotations__ = annotations


def draw_options(layout, operator, spec):
    """Blender 내보내기 패널과 같은 순서·묶음으로 옵션을 그린다."""
    properties = spec.rna_properties()

    for panel, names in spec.layout_groups():
        body = _panel_body(layout, spec, panel, operator)
        if body is None:
            continue
        for name in names:
            prop = properties.get(name)
            if prop is not None and _is_enum_flag(prop):
                # Blender 내보내기 패널과 같게 열거형 다중 선택은 별도 열에 그린다.
                body.column().prop(operator, name)
            else:
                body.prop(operator, name)


def _panel_body(layout, spec, panel, operator):
    """패널 헤더를 그리고 본문 레이아웃을 돌려준다. 접혀 있으면 None."""
    if panel.title is None:
        return layout

    try:
        header, body = layout.panel(
            f"cat_export_{spec.key}_{panel.title.lower()}",
            default_closed=panel.default_closed,
        )
    except (AttributeError, TypeError, RuntimeError):
        # 접이식 패널을 쓸 수 없는 환경에서는 아래 대체 레이아웃으로 넘어간다.
        header = body = None

    if header is not None:
        if panel.toggle:
            header.use_property_split = False
            header.prop(operator, panel.toggle, text="")
        header.label(text=panel.title)
        if body is not None and panel.toggle:
            body.enabled = getattr(operator, panel.toggle)
        return body

    # `UILayout.panel()`을 쓸 수 없는 환경을 위한 대체 레이아웃
    box = layout.box()
    box.label(text=panel.title)
    if panel.toggle:
        box.prop(operator, panel.toggle)
        box.enabled = getattr(operator, panel.toggle)
    return box


# ---------------------------------------------------------------------------
# 내보내기 종류별 정의
# ---------------------------------------------------------------------------

FBX_KEY = "fbx"
OBJ_KEY = "obj"

FBX_SPEC = ExporterSpec(
    key=FBX_KEY,
    op_path="export_scene.fbx",
    extension=".fbx",
    forced_kwargs={"use_selection": True},
    skip_props=(
        # 파일 브라우저 전용이거나 CAT 내보내기 흐름에서 의미가 없는 항목
        "filepath", "check_existing", "filter_glob", "ui_tab",
        "use_visible", "use_active_collection", "collection",
        "batch_mode", "use_batch_own_dir",
        # Blender 내보내기 패널에서도 그리지 않는 항목
        "use_mesh_modifiers_render",
    ),
    panels=(
        PanelDef(None, False, None, ("path_mode", "embed_textures")),
        PanelDef("Include", False, None, ("object_types", "use_custom_props")),
        PanelDef("Transform", False, None, (
            "global_scale", "apply_scale_options", "axis_forward", "axis_up",
            "apply_unit_scale", "use_space_transform", "bake_space_transform",
        )),
        PanelDef("Geometry", True, None, (
            "mesh_smooth_type", "use_subsurf", "use_mesh_modifiers", "use_mesh_edges",
            "use_triangles", "use_tspace", "colors_type", "prioritize_active_color",
        )),
        PanelDef("Armature", True, None, (
            "primary_bone_axis", "secondary_bone_axis", "armature_nodetype",
            "use_armature_deform_only", "add_leaf_bones",
        )),
        PanelDef("Animation", True, "bake_anim", (
            "bake_anim_use_all_bones", "bake_anim_use_nla_strips", "bake_anim_use_all_actions",
            "bake_anim_force_startend_keying", "bake_anim_step", "bake_anim_simplify_factor",
        )),
    ),
)

OBJ_SPEC = ExporterSpec(
    key=OBJ_KEY,
    op_path="wm.obj_export",
    extension=".obj",
    forced_kwargs={"export_selected_objects": True},
    skip_props=("filepath", "check_existing"),
    panels=(
        PanelDef("Transform", False, None, (
            "global_scale", "forward_axis", "up_axis", "apply_transform",
        )),
        PanelDef("Geometry", False, None, (
            "apply_modifiers", "export_eval_mode", "export_uv", "export_normals",
            "export_colors", "export_triangulated_mesh", "export_curves_as_nurbs",
        )),
        PanelDef("Materials", True, None, (
            "export_materials", "export_pbr_extensions", "path_mode",
        )),
        PanelDef("Grouping", True, None, (
            "export_object_groups", "export_material_groups", "export_vertex_groups",
            "export_smooth_groups", "smooth_group_bitflags",
        )),
        PanelDef("Animation", True, "export_animation", ("start_frame", "end_frame")),
    ),
)

SPECS = {
    FBX_KEY: FBX_SPEC,
    OBJ_KEY: OBJ_SPEC,
}
