import importlib
import os
import pathlib
import sys

import addon_utils
import bpy


def fail(message):
    print(f"[CAT Menus] {message}", file=sys.stderr)
    raise SystemExit(1)


addon_id = os.environ.get("CATMENUS_ADDON_ID", "cat_menus")
source_dir = pathlib.Path(os.environ.get("CATMENUS_SOURCE_DIR", "")).resolve()
if not source_dir or not (source_dir / "blender_manifest.toml").exists():
    fail(f"소스 경로에 blender_manifest.toml이 없습니다: {source_dir}")

module_name = f"bl_ext.user_default.{addon_id}"
user_resource = pathlib.Path(bpy.utils.resource_path("USER")).resolve()
expected_link = (user_resource / "extensions" / "user_default" / addon_id).resolve()

print(f"[CAT Menus] USER={user_resource}")
print(f"[CAT Menus] SOURCE={source_dir}")
print(f"[CAT Menus] EXTENSION={expected_link}")

if expected_link != source_dir:
    fail(f"개발 Extension 링크가 소스 루트를 가리키지 않습니다: {expected_link}")

enabled_default, enabled_state = addon_utils.check(module_name)
if not enabled_state:
    try:
        addon_utils.enable(module_name, default_set=True, persistent=True)
    except Exception as exc:
        fail(f"Extension 활성화 실패: {module_name}: {exc}")

module = importlib.import_module(module_name)
if not hasattr(module, "register") or not hasattr(module, "unregister"):
    fail(f"register/unregister 함수를 찾을 수 없습니다: {module_name}")

bpy.ops.wm.save_userpref()
print(f"[CAT Menus] 활성화 완료: {module_name}")
