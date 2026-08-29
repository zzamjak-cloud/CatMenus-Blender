import bpy

bl_info = {
    "name": "CatMenus",
    "author": "Woody",
    "version": (0, 1, 1),
    "blender": (4, 2, 0),
    "description": "캐주얼G팀 CAT 메뉴 제작에 필요한 애드온입니다.",
    "doc_url": "https://treenod.atlassian.net/wiki/spaces/CGP/pages/71737541370/CAT",
    "category": "3D View",
}

from .menu import CatMenusMenu, menu_func
from .operators import OPERATOR_CLASSES

CLASSES = (
    CatMenusMenu,
    *OPERATOR_CLASSES,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
