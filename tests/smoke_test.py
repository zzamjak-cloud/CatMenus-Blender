import importlib
import pathlib
import sys

import addon_utils
import bpy


ADDON_ID = "cat_menus"
MODULE_NAME = f"bl_ext.user_default.{ADDON_ID}"


def fail(message):
    print(f"[CAT Menus Smoke] {message}", file=sys.stderr)
    raise SystemExit(1)


def assert_operator(idname):
    prefix, name = idname.split(".", 1)
    if not hasattr(getattr(bpy.ops, prefix), name):
        fail(f"연산자가 등록되지 않았습니다: {idname}")


def main():
    user_resource = pathlib.Path(bpy.utils.resource_path("USER")).resolve()
    print(f"[CAT Menus Smoke] USER={user_resource}")

    enabled_default, enabled_state = addon_utils.check(MODULE_NAME)
    if not enabled_state:
        addon_utils.enable(MODULE_NAME, default_set=True, persistent=True)

    module = importlib.import_module(MODULE_NAME)
    manifest = read_manifest()
    if manifest["id"] != ADDON_ID:
        fail(f"manifest id가 다릅니다: {manifest['id']} != {ADDON_ID}")
    if not hasattr(module, "CLASSES"):
        fail("등록 클래스 목록을 찾을 수 없습니다: CLASSES")

    expected = [
        "object.match_name",
        "object.block_sort",
        "object.collision_maker",
        "object.picking",
        "object.exportuv",
        "object.export_obj",
        "object.export_fbx",
        "object.clean_settings",
        "object.block_rotation_info",
        "object.mission_icon_maker",
    ]
    for idname in expected:
        assert_operator(idname)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(3, 0, 0))
    first = bpy.context.object
    first.name = "B_02"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(4, 0, 0))
    second = bpy.context.object
    second.name = "A_01"
    first.select_set(True)
    second.select_set(True)
    bpy.context.view_layer.objects.active = second
    result = bpy.ops.object.block_sort(column=2)
    if result != {"FINISHED"}:
        fail(f"BlockSort 실행 실패: {result}")

    bpy.ops.object.select_all(action="SELECT")
    result = bpy.ops.object.match_name()
    if result != {"FINISHED"}:
        fail(f"MatchName 실행 실패: {result}")

    addon_utils.disable(MODULE_NAME, default_set=True)
    print("[CAT Menus Smoke] 통과")


def read_manifest():
    import tomllib

    module = importlib.import_module(MODULE_NAME)
    manifest_path = pathlib.Path(module.__file__).resolve().parent / "blender_manifest.toml"
    return tomllib.loads(manifest_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
