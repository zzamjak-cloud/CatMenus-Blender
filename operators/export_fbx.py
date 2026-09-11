"""FBX 프리셋 내보내기 연산자.

옵션은 Blender의 `export_scene.fbx` 연산자에서 그대로 복제하므로 대화창 항목이
Blender 기본 FBX 내보내기 설정과 같다. 자세한 내용은 `export_presets` 참고.
"""

import bpy

from .. import export_presets
from .export_preset_base import (
    ExportPresetAdd,
    ExportPresetEdit,
    ExportPresetRemove,
    ExportPresetRun,
)


class ExportFBX(ExportPresetRun, bpy.types.Operator):
    """선택한 오브젝트를 프리셋 설정으로 FBX 파일로 추출합니다."""
    bl_idname = "object.export_fbx"
    bl_label = "Export FBX"

    spec = export_presets.FBX_SPEC


class ExportFBXPresetAdd(ExportPresetAdd, bpy.types.Operator):
    """새 FBX 내보내기 프리셋을 만들어 로컬에 저장합니다."""
    bl_idname = "object.export_fbx_preset_add"
    bl_label = "프리셋"

    spec = export_presets.FBX_SPEC


class ExportFBXPresetEdit(ExportPresetEdit, bpy.types.Operator):
    """저장된 FBX 내보내기 프리셋의 이름과 옵션을 수정합니다."""
    bl_idname = "object.export_fbx_preset_edit"
    bl_label = "프리셋 수정"

    spec = export_presets.FBX_SPEC


class ExportFBXPresetRemove(ExportPresetRemove, bpy.types.Operator):
    """저장된 FBX 내보내기 프리셋을 삭제합니다."""
    bl_idname = "object.export_fbx_preset_remove"
    bl_label = "프리셋 삭제"

    spec = export_presets.FBX_SPEC
