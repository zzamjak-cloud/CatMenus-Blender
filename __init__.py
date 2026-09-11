import bpy

bl_info = {
    "name": "CatMenus",
    "author": "Woody",
    "version": (0, 4, 0),
    "blender": (4, 2, 0),
    "description": "캐주얼G팀 CAT 메뉴 제작에 필요한 애드온입니다.",
    "doc_url": "https://treenod.atlassian.net/wiki/spaces/CGP/pages/71737541370/CAT",
    "category": "3D View",
}

from .menu import CatMenusMenu, ExportFBXPresetMenu, ExportOBJPresetMenu, menu_func
from .operators import OPERATOR_CLASSES, prepare_preset_dialogs

CLASSES = (
    CatMenusMenu,
    ExportOBJPresetMenu,
    ExportFBXPresetMenu,
    *OPERATOR_CLASSES,
)


def register():
    # 프리셋 대화창 옵션은 Blender 내보내기 연산자에서 복제하므로 등록 전에 붙인다.
    prepare_preset_dialogs()

    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
