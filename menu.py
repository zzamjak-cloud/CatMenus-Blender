import bpy

from .operators import (
    BlockRotationInfo,
    BlockSort,
    CleanSetting,
    CollisionMaker,
    ExportFBX,
    ExportOBJ,
    ExportUV,
    MatchName,
    MissionIconMaker,
    PickingMaker,
)


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
        layout.operator(ExportFBX.bl_idname, text=ExportFBX.bl_label, icon='EXPORT') # Export FBX
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
