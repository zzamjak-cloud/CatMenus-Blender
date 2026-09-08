import bpy

from . import fbx_presets
from .operators import (
    BlockRotationInfo,
    BlockSort,
    CleanSetting,
    CollisionMaker,
    ExportFBX,
    ExportFBXPresetAdd,
    ExportFBXPresetRemove,
    ExportOBJ,
    ExportUV,
    MatchName,
    MissionIconMaker,
    PickingMaker,
)


class ExportFBXPresetMenu(bpy.types.Menu):
    """로컬에 저장된 FBX 내보내기 프리셋 목록"""
    bl_idname = "OBJECT_MT_cat_menus_export_fbx_presets"
    bl_label = "Export FBX"

    def draw(self, context):
        layout = self.layout

        names = fbx_presets.preset_names()
        if not names:
            layout.label(text="등록된 프리셋이 없습니다", icon='INFO')

        for name in names:
            row = layout.row(align=True)
            # 프리셋으로 즉시 내보내기
            run = row.operator(ExportFBX.bl_idname, text=name, icon='EXPORT')
            run.preset_name = name
            # 프리셋 삭제
            remove = row.operator(ExportFBXPresetRemove.bl_idname, text="", icon='X', emboss=False)
            remove.preset_name = name

        layout.separator()
        layout.operator(ExportFBXPresetAdd.bl_idname, text=ExportFBXPresetAdd.bl_label, icon='ADD') # +프리셋


class CatMenusMenu(bpy.types.Menu):
    """CAT 블럭 제작을 위한 기능들"""
    bl_idname = "OBJECT_MT_cat_menus_menu"
    bl_label = "Cat"

    def draw(self, context):
        layout = self.layout
            # MatchName & BlockSort
        layout.operator(MatchName.bl_idname, text=MatchName.bl_label, icon='SORTALPHA') # Match Name
        layout.operator(BlockSort.bl_idname, text=BlockSort.bl_label, icon="SNAP_VERTEX") # Block Sort
        layout.separator()
            # Export UV / OBJ / FBX
        layout.operator(ExportUV.bl_idname, text=ExportUV.bl_label, icon="TEXTURE") # Export UV
        layout.operator(ExportOBJ.bl_idname, text=ExportOBJ.bl_label, icon='EXPORT') # Export OBJ
        layout.menu(ExportFBXPresetMenu.bl_idname, text=ExportFBXPresetMenu.bl_label, icon='EXPORT') # Export FBX 프리셋 하위 메뉴
        layout.separator()
            # Colission / Picking
        layout.operator(CollisionMaker.bl_idname, text=CollisionMaker.bl_label, icon='CUBE') # Collision Maker
        layout.operator(PickingMaker.bl_idname, text=PickingMaker.bl_label, icon='MESH_CUBE') # Picking Maker
        layout.separator()
            # Clean Setting / Rotation Info / Mission Icon
        layout.operator(CleanSetting.bl_idname, text=CleanSetting.bl_label, icon='BRUSH_DATA') # Clean Setting
        layout.operator(BlockRotationInfo.bl_idname, text=BlockRotationInfo.bl_label, icon='INFO') # Block Rotation Info
        layout.operator(MissionIconMaker.bl_idname, text=MissionIconMaker.bl_label, icon='OUTLINER_OB_CAMERA') # Mission Icon Maker
        layout.separator()


def menu_func(self, context):
    self.layout.menu(CatMenusMenu.bl_idname, text=CatMenusMenu.bl_label)
