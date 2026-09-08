import importlib
import pathlib
import shutil
import sys
import tempfile

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
        "object.export_fbx_preset_add",
        "object.export_fbx_preset_remove",
        "object.clean_settings",
        "object.block_rotation_info",
        "object.mission_icon_maker",
    ]
    for idname in expected:
        assert_operator(idname)

    # 메뉴 클래스 등록 확인
    for menu_idname in ("OBJECT_MT_cat_menus_menu", "OBJECT_MT_cat_menus_export_fbx_presets"):
        if not hasattr(bpy.types, menu_idname):
            fail(f"메뉴가 등록되지 않았습니다: {menu_idname}")

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

    check_fbx_presets()
    check_menu_draw()

    addon_utils.disable(MODULE_NAME, default_set=True)
    print("[CAT Menus Smoke] 통과")


def check_fbx_presets():
    """FBX 프리셋 등록·내보내기·삭제 왕복을 검증한다."""
    fbx_presets = importlib.import_module(f"{MODULE_NAME}.fbx_presets")

    preset_path = pathlib.Path(fbx_presets.preset_file_path())
    if not str(preset_path):
        fail("프리셋 저장 경로를 확보하지 못했습니다.")

    # 기존 프리셋 파일이 있으면 백업해 두고 테스트 후 복원한다.
    backup = preset_path.with_suffix(".json.smoke_backup")
    if preset_path.exists():
        shutil.copy2(preset_path, backup)

    preset_name = "CAT Smoke Preset"
    try:
        result = bpy.ops.object.export_fbx_preset_add(
            'EXEC_DEFAULT',
            preset_name=preset_name,
            export_subdir="FBX_SMOKE",
            object_types={'MESH'},
            mesh_smooth_type='EDGE',
            use_triangles=True,
            global_scale=2.0,
        )
        if result != {"FINISHED"}:
            fail(f"프리셋 등록 실패: {result}")

        if not preset_path.exists():
            fail(f"프리셋 파일이 만들어지지 않았습니다: {preset_path}")

        if preset_name not in fbx_presets.preset_names():
            fail(f"등록한 프리셋이 목록에 없습니다: {preset_name}")

        stored = fbx_presets.get_preset(preset_name)
        for key, expected in (
            ("export_subdir", "FBX_SMOKE"),
            ("mesh_smooth_type", "EDGE"),
            ("use_triangles", True),
            ("global_scale", 2.0),
        ):
            if stored[key] != expected:
                fail(f"프리셋 값이 다릅니다: {key}={stored[key]!r} != {expected!r}")

        # 프리셋 이름 없이 실행하면 오류 리포트와 함께 취소되어야 한다.
        try:
            result = bpy.ops.object.export_fbx('EXEC_DEFAULT', preset_name="")
        except RuntimeError:
            pass
        else:
            fail(f"프리셋 미선택 실행이 취소되지 않았습니다: {result}")

        with tempfile.TemporaryDirectory() as temp_dir:
            blend_path = pathlib.Path(temp_dir) / "smoke.blend"
            bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add(size=1)
            cube = bpy.context.object
            cube.name = "SmokeCube"
            cube.select_set(True)

            result = bpy.ops.object.export_fbx('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"프리셋 내보내기 실패: {result}")

            exported = blend_path.parent / "FBX_SMOKE" / "SmokeCube.fbx"
            if not exported.is_file():
                fail(f"FBX 파일이 생성되지 않았습니다: {exported}")

            if not cube.select_get():
                fail("내보내기 후 선택 상태가 복원되지 않았습니다.")

        check_fixed_export_dir(fbx_presets)

        result = bpy.ops.object.export_fbx_preset_remove('EXEC_DEFAULT', preset_name=preset_name)
        if result != {"FINISHED"}:
            fail(f"프리셋 삭제 실패: {result}")

        if preset_name in fbx_presets.preset_names():
            fail(f"삭제한 프리셋이 남아 있습니다: {preset_name}")
    finally:
        if backup.exists():
            shutil.move(str(backup), str(preset_path))
        elif preset_path.exists():
            preset_path.unlink()

    print("[CAT Menus Smoke] FBX 프리셋 왕복 통과")


class DrawHost:
    """draw() 함수에 넘길 self 대역. layout만 제공한다."""

    def __init__(self, layout, op_idname=None):
        self.layout = layout
        self.op_idname = op_idname

    def __getattr__(self, name):
        # draw()가 읽는 연산자 프로퍼티는 RNA 기본값으로 대신한다.
        idname = self.__dict__.get("op_idname")
        prop = resolve_operator_property(idname, name) if idname else None
        if prop is None:
            fail(f"draw()가 없는 속성을 읽었습니다: {idname}.{name}")
        return getattr(prop, "default", "")


class StubOperatorProps:
    """layout.operator() 반환값 대역. 설정하는 프로퍼티가 실제로 있는지 검증한다."""

    def __init__(self, idname):
        object.__setattr__(self, "idname", idname)
        object.__setattr__(self, "assigned", {})

    def __setattr__(self, name, value):
        if resolve_operator_property(self.idname, name) is None:
            fail(f"연산자 프로퍼티가 없습니다: {self.idname}.{name}")
        self.assigned[name] = value


class StubLayout:
    """UI 없이 draw() 코드 경로를 실행하기 위한 최소 UILayout 대역."""

    def __init__(self, log):
        self.log = log
        self.use_property_split = False
        self.use_property_decorate = False

    def _child(self):
        return StubLayout(self.log)

    def row(self, **kwargs):
        return self._child()

    def column(self, **kwargs):
        return self._child()

    def separator(self, **kwargs):
        pass

    def label(self, **kwargs):
        self.log.append(("label", kwargs.get("text", "")))

    def menu(self, idname, **kwargs):
        if not hasattr(bpy.types, idname):
            fail(f"하위 메뉴가 등록되지 않았습니다: {idname}")
        self.log.append(("menu", idname))

    def operator(self, idname, **kwargs):
        assert_operator(idname)
        self.log.append(("operator", idname, kwargs.get("text", "")))
        return StubOperatorProps(idname)

    def prop(self, data, name, **kwargs):
        idname = getattr(data, "op_idname", None)
        if idname is None:
            fail(f"prop 대상이 연산자가 아닙니다: {name}")
        if resolve_operator_property(idname, name) is None:
            fail(f"연산자 프로퍼티가 없습니다: {idname}.{name}")
        self.log.append(("prop", name))


def resolve_operator_property(idname, name):
    """연산자 idname과 프로퍼티 이름으로 RNA 프로퍼티를 찾는다."""
    prefix, op_name = idname.split(".", 1)
    operator = getattr(getattr(bpy.ops, prefix), op_name)
    return operator.get_rna_type().properties.get(name)


def check_fixed_export_dir(fbx_presets):
    """프리셋에 지정한 폴더로 곧바로 내보내는지 검증한다."""
    preset_name = "CAT Fixed Dir Preset"

    with tempfile.TemporaryDirectory() as temp_dir:
        fixed_dir = pathlib.Path(temp_dir) / "fixed_export"

        result = bpy.ops.object.export_fbx_preset_add(
            'EXEC_DEFAULT',
            preset_name=preset_name,
            export_dir=str(fixed_dir),
            export_subdir="SHOULD_NOT_BE_USED",
        )
        if result != {"FINISHED"}:
            fail(f"폴더 지정 프리셋 등록 실패: {result}")

        stored = fbx_presets.get_preset(preset_name)
        if stored["export_dir"] != str(fixed_dir):
            fail(f"내보내기 폴더가 저장되지 않았습니다: {stored['export_dir']!r}")

        resolved, error = fbx_presets.resolve_export_dir(stored, bpy.data.filepath)
        if error:
            fail(f"내보내기 폴더를 계산하지 못했습니다: {error}")
        if pathlib.Path(resolved) != fixed_dir:
            fail(f"지정한 폴더가 무시되었습니다: {resolved}")

        try:
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add(size=1)
            cube = bpy.context.object
            cube.name = "FixedDirCube"
            cube.select_set(True)

            result = bpy.ops.object.export_fbx('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"폴더 지정 프리셋 내보내기 실패: {result}")

            exported = fixed_dir / "FixedDirCube.fbx"
            if not exported.is_file():
                fail(f"지정한 폴더에 FBX가 생성되지 않았습니다: {exported}")

            blend_sibling = pathlib.Path(bpy.data.filepath).parent / "SHOULD_NOT_BE_USED"
            if blend_sibling.exists():
                fail(f"폴더를 지정했는데도 블렌드 파일 옆 폴더가 만들어졌습니다: {blend_sibling}")

            # 폴더를 비운 프리셋은 블렌드 파일이 없으면 오류를 내야 한다.
            empty = dict(stored)
            empty["export_dir"] = ""
            _, error = fbx_presets.resolve_export_dir(empty, "")
            if not error:
                fail("블렌드 파일이 없고 폴더도 비었는데 오류가 나지 않았습니다.")
        finally:
            fbx_presets.remove_preset(preset_name)

    print("[CAT Menus Smoke] 지정 폴더 내보내기 통과")


def check_menu_draw():
    """메뉴와 +프리셋 대화창의 draw() 경로를 UI 없이 실행한다."""
    menu_module = importlib.import_module(f"{MODULE_NAME}.menu")
    fbx_presets = importlib.import_module(f"{MODULE_NAME}.fbx_presets")

    preset_name = "CAT Draw Preset"
    saved, _ = fbx_presets.add_preset(preset_name, dict(fbx_presets.DEFAULT_PRESET))
    if not saved:
        fail("draw 검증용 프리셋을 저장하지 못했습니다.")

    try:
        # 프리셋이 있을 때: 실행 항목과 삭제 항목, +프리셋 항목이 모두 나와야 한다.
        log = []
        menu_module.ExportFBXPresetMenu.draw(DrawHost(StubLayout(log)), bpy.context)
        operators = [entry for entry in log if entry[0] == "operator"]
        texts = [entry[2] for entry in operators]
        if preset_name not in texts:
            fail(f"하위 메뉴에 프리셋이 표시되지 않았습니다: {texts}")
        idnames = {entry[1] for entry in operators}
        for expected in ("object.export_fbx", "object.export_fbx_preset_add", "object.export_fbx_preset_remove"):
            if expected not in idnames:
                fail(f"하위 메뉴에 항목이 없습니다: {expected}")

        # 프리셋이 없을 때: 안내 라벨과 +프리셋만 남아야 한다.
        fbx_presets.remove_preset(preset_name)
        log = []
        menu_module.ExportFBXPresetMenu.draw(DrawHost(StubLayout(log)), bpy.context)
        if not any(entry[0] == "label" for entry in log):
            fail("프리셋이 없을 때 안내 라벨이 표시되지 않았습니다.")
        if any(entry[0] == "operator" and entry[1] == "object.export_fbx" for entry in log):
            fail("프리셋이 없는데 내보내기 항목이 표시되었습니다.")

        # CAT 메뉴가 Export FBX를 하위 메뉴로 연결하는지 확인한다.
        log = []
        menu_module.CatMenusMenu.draw(DrawHost(StubLayout(log)), bpy.context)
        if ("menu", menu_module.ExportFBXPresetMenu.bl_idname) not in log:
            fail("CAT 메뉴에 Export FBX 하위 메뉴가 없습니다.")
        if any(entry[0] == "operator" and entry[1] == "object.export_fbx" for entry in log):
            fail("CAT 메뉴에 Export FBX 연산자가 직접 남아 있습니다.")

        # +프리셋 대화창 draw 경로
        export_fbx = importlib.import_module(f"{MODULE_NAME}.operators.export_fbx")
        log = []
        add_class = export_fbx.ExportFBXPresetAdd
        add_class.draw(DrawHost(StubLayout(log), add_class.bl_idname), bpy.context)
        drawn = {entry[1] for entry in log if entry[0] == "prop"}
        missing = {"preset_name", "export_dir", "export_subdir", "object_types"} - drawn
        if missing:
            fail(f"+프리셋 대화창에 빠진 프로퍼티가 있습니다: {sorted(missing)}")
    finally:
        fbx_presets.remove_preset(preset_name)

    print("[CAT Menus Smoke] 메뉴 draw 통과")


def read_manifest():
    import tomllib

    module = importlib.import_module(MODULE_NAME)
    manifest_path = pathlib.Path(module.__file__).resolve().parent / "blender_manifest.toml"
    return tomllib.loads(manifest_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
