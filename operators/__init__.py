from .. import export_presets
from .match_name import MatchName
from .block_sort import BlockSort
from .export_uv import ExportUV
from .export_obj import (
    ExportOBJ,
    ExportOBJPresetAdd,
    ExportOBJPresetEdit,
    ExportOBJPresetRemove,
)
from .export_fbx import (
    ExportFBX,
    ExportFBXPresetAdd,
    ExportFBXPresetEdit,
    ExportFBXPresetRemove,
)
from .collision_maker import CollisionMaker
from .clean_setting import CleanSetting
from .block_rotation_info import BlockRotationInfo
from .mission_icon_maker import MissionIconMaker

OPERATOR_CLASSES = (
    BlockSort,
    MatchName,
    ExportUV,
    ExportOBJ,
    ExportOBJPresetAdd,
    ExportOBJPresetEdit,
    ExportOBJPresetRemove,
    ExportFBX,
    ExportFBXPresetAdd,
    ExportFBXPresetEdit,
    ExportFBXPresetRemove,
    CollisionMaker,
    CleanSetting,
    BlockRotationInfo,
    MissionIconMaker,
)

# 프리셋 등록·수정 대화창과 짝이 되는 내보내기 정의
PRESET_DIALOGS = (
    (ExportFBXPresetAdd, export_presets.FBX_SPEC),
    (ExportFBXPresetEdit, export_presets.FBX_SPEC),
    (ExportOBJPresetAdd, export_presets.OBJ_SPEC),
    (ExportOBJPresetEdit, export_presets.OBJ_SPEC),
)


def prepare_preset_dialogs():
    """프리셋 등록·수정 대화창에 Blender 내보내기 옵션 프로퍼티를 붙인다.

    Blender 연산자 RNA를 읽어야 하므로 클래스 등록 직전에 호출해야 한다.
    """
    for cls, spec in PRESET_DIALOGS:
        export_presets.apply_dialog_properties(cls, spec)
