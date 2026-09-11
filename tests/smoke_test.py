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
        "object.exportuv",
        "object.export_obj",
        "object.export_obj_preset_add",
        "object.export_obj_preset_edit",
        "object.export_obj_preset_remove",
        "object.export_fbx",
        "object.export_fbx_preset_add",
        "object.export_fbx_preset_edit",
        "object.export_fbx_preset_remove",
        "object.clean_settings",
        "object.block_rotation_info",
        "object.mission_icon_maker",
    ]
    for idname in expected:
        assert_operator(idname)

    # 메뉴 클래스 등록 확인
    for menu_idname in (
        "OBJECT_MT_cat_menus_menu",
        "OBJECT_MT_cat_menus_export_fbx_presets",
        "OBJECT_MT_cat_menus_export_obj_presets",
    ):
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

    check_rna_mirror()
    with preset_store_backup():
        for case in EXPORT_CASES:
            check_preset_roundtrip(case)
        check_menu_draw()

    addon_utils.disable(MODULE_NAME, default_set=True)
    print("[CAT Menus Smoke] 통과")


def export_presets_module():
    return importlib.import_module(f"{MODULE_NAME}.export_presets")


class ExportCase:
    """내보내기 종류 하나에 대한 검증 설정."""

    def __init__(self, key, run_idname, add_idname, edit_idname, remove_idname, extension, sample):
        self.key = key
        self.run_idname = run_idname
        self.add_idname = add_idname
        self.edit_idname = edit_idname
        self.remove_idname = remove_idname
        self.extension = extension
        self.sample = sample  # 저장·복원을 확인할 옵션 값


EXPORT_CASES = (
    ExportCase(
        key="fbx",
        run_idname="object.export_fbx",
        add_idname="object.export_fbx_preset_add",
        edit_idname="object.export_fbx_preset_edit",
        remove_idname="object.export_fbx_preset_remove",
        extension=".fbx",
        sample={
            "object_types": {'MESH'},
            "mesh_smooth_type": 'EDGE',
            "use_triangles": True,
            "global_scale": 2.0,
            # 애니메이션 옵션도 프리셋에 저장되어야 한다.
            "bake_anim": True,
            "bake_anim_use_nla_strips": False,
            "bake_anim_step": 2.0,
        },
    ),
    ExportCase(
        key="obj",
        run_idname="object.export_obj",
        add_idname="object.export_obj_preset_add",
        edit_idname="object.export_obj_preset_edit",
        remove_idname="object.export_obj_preset_remove",
        extension=".obj",
        sample={
            "export_triangulated_mesh": True,
            "export_materials": False,
            "global_scale": 2.0,
            "forward_axis": 'X',
        },
    ),
)


class preset_store_backup:
    """프리셋 저장 파일을 백업했다가 검증이 끝나면 되돌린다."""

    def __enter__(self):
        export_presets = export_presets_module()
        self.path = pathlib.Path(export_presets.preset_file_path())
        if not str(self.path):
            fail("프리셋 저장 경로를 확보하지 못했습니다.")
        self.backup = self.path.with_suffix(".json.smoke_backup")
        if self.path.exists():
            shutil.copy2(self.path, self.backup)
        return self

    def __exit__(self, *exc_info):
        if self.backup.exists():
            shutil.move(str(self.backup), str(self.path))
        elif self.path.exists():
            self.path.unlink()
        return False


def check_rna_mirror():
    """대화창 옵션이 Blender 내보내기 연산자 옵션과 같은지 확인한다."""
    export_presets = export_presets_module()

    for case in EXPORT_CASES:
        spec = export_presets.SPECS[case.key]
        if not spec.is_available():
            fail(f"내보내기 연산자 RNA를 읽지 못했습니다: {spec.op_path}")

        source = spec.rna_properties()

        # 프리셋에 담기는 모든 옵션이 등록·수정 대화창 프로퍼티로도 존재해야 한다.
        for idname in (case.add_idname, case.edit_idname):
            dialog = resolve_operator_properties(idname)
            for name in spec.option_names():
                if name not in dialog:
                    fail(f"대화창에 옵션이 없습니다: {idname}.{name}")
                if dialog[name].name != source[name].name:
                    fail(
                        f"옵션 라벨이 Blender와 다릅니다: {name}: "
                        f"{dialog[name].name!r} != {source[name].name!r}"
                    )

        # Blender가 제공하는 옵션 중 제외 목록에 없는 것이 빠지면 안 된다.
        exposed = set(spec.option_names())
        for name, prop in source.items():
            if name in spec.skip_props or name in spec.forced_kwargs:
                continue
            if prop.is_hidden or prop.is_readonly:
                continue
            if prop.type not in {'BOOLEAN', 'ENUM', 'FLOAT', 'INT', 'STRING'}:
                continue
            if getattr(prop, "array_length", 0):
                continue
            if name not in exposed:
                fail(f"프리셋에서 빠진 내보내기 옵션이 있습니다: {spec.op_path}.{name}")

    # FBX 애니메이션 옵션이 실제로 모두 들어왔는지 못 박아 둔다.
    fbx_options = set(export_presets.FBX_SPEC.option_names())
    animation_options = {
        "bake_anim",
        "bake_anim_use_all_bones",
        "bake_anim_use_nla_strips",
        "bake_anim_use_all_actions",
        "bake_anim_force_startend_keying",
        "bake_anim_step",
        "bake_anim_simplify_factor",
    }
    missing = animation_options - fbx_options
    if missing:
        fail(f"FBX 애니메이션 옵션이 빠졌습니다: {sorted(missing)}")

    print("[CAT Menus Smoke] Blender 내보내기 옵션 동기화 통과")


def check_preset_roundtrip(case):
    """프리셋 등록·내보내기·삭제 왕복을 검증한다."""
    export_presets = export_presets_module()
    preset_path = pathlib.Path(export_presets.preset_file_path())

    preset_name = f"CAT Smoke {case.key.upper()}"
    add_operator = resolve_operator(case.add_idname)
    run_operator = resolve_operator(case.run_idname)
    remove_operator = resolve_operator(case.remove_idname)

    try:
        result = add_operator('EXEC_DEFAULT', preset_name=preset_name, export_dir="", **case.sample)
        if result != {"FINISHED"}:
            fail(f"프리셋 등록 실패: {case.key}: {result}")

        if not preset_path.exists():
            fail(f"프리셋 파일이 만들어지지 않았습니다: {preset_path}")

        if preset_name not in export_presets.preset_names(case.key):
            fail(f"등록한 프리셋이 목록에 없습니다: {preset_name}")

        stored = export_presets.get_preset(case.key, preset_name)
        if stored["export_dir"] != "":
            fail(f"내보내기 폴더가 비어 있지 않습니다: {stored['export_dir']!r}")
        for key, expected in case.sample.items():
            actual = stored[key]
            if isinstance(expected, set):
                actual = set(actual)
            if actual != expected:
                fail(f"프리셋 값이 다릅니다: {case.key}.{key}={actual!r} != {expected!r}")

        # 프리셋 이름 없이 실행하면 오류 리포트와 함께 취소되어야 한다.
        try:
            result = run_operator('EXEC_DEFAULT', preset_name="")
        except RuntimeError:
            pass
        else:
            fail(f"프리셋 미선택 실행이 취소되지 않았습니다: {case.key}: {result}")

        with tempfile.TemporaryDirectory() as temp_dir:
            blend_path = pathlib.Path(temp_dir) / "smoke.blend"
            bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add(size=1)
            cube = bpy.context.object
            cube.name = "SmokeCube"
            cube.select_set(True)

            result = run_operator('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"프리셋 내보내기 실패: {case.key}: {result}")

            # 폴더를 비운 프리셋은 하위 폴더 없이 블렌드 파일이 있는 폴더에 바로 내보낸다.
            exported = blend_path.parent / f"SmokeCube{case.extension}"
            if not exported.is_file():
                fail(f"파일이 생성되지 않았습니다: {exported}")

            subdirs = [child.name for child in blend_path.parent.iterdir() if child.is_dir()]
            if subdirs:
                fail(f"하위 폴더가 만들어졌습니다: {subdirs}")

            if not cube.select_get():
                fail("내보내기 후 선택 상태가 복원되지 않았습니다.")

        check_fixed_export_dir(case)
        check_single_file_mode(case)
        check_invalid_object_name(case)
        check_export_failure(case)
        check_preset_edit(case)

        result = remove_operator('EXEC_DEFAULT', preset_name=preset_name)
        if result != {"FINISHED"}:
            fail(f"프리셋 삭제 실패: {case.key}: {result}")

        if preset_name in export_presets.preset_names(case.key):
            fail(f"삭제한 프리셋이 남아 있습니다: {preset_name}")
    finally:
        export_presets.remove_preset(case.key, preset_name)

    print(f"[CAT Menus Smoke] {case.key.upper()} 프리셋 왕복 통과")


def check_fixed_export_dir(case):
    """프리셋에 지정한 폴더로 곧바로 내보내는지 검증한다."""
    export_presets = export_presets_module()
    preset_name = f"CAT Fixed Dir {case.key.upper()}"

    with tempfile.TemporaryDirectory() as temp_dir:
        fixed_dir = pathlib.Path(temp_dir) / "fixed_export"

        result = resolve_operator(case.add_idname)(
            'EXEC_DEFAULT',
            preset_name=preset_name,
            export_dir=str(fixed_dir),
        )
        if result != {"FINISHED"}:
            fail(f"폴더 지정 프리셋 등록 실패: {case.key}: {result}")

        stored = export_presets.get_preset(case.key, preset_name)
        if stored["export_dir"] != str(fixed_dir):
            fail(f"내보내기 폴더가 저장되지 않았습니다: {stored['export_dir']!r}")

        resolved, error = export_presets.resolve_export_dir(stored, bpy.data.filepath)
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

            result = resolve_operator(case.run_idname)('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"폴더 지정 프리셋 내보내기 실패: {case.key}: {result}")

            exported = fixed_dir / f"FixedDirCube{case.extension}"
            if not exported.is_file():
                fail(f"지정한 폴더에 파일이 생성되지 않았습니다: {exported}")

            if [child.name for child in fixed_dir.iterdir() if child.is_dir()]:
                fail(f"지정한 폴더 안에 하위 폴더가 만들어졌습니다: {fixed_dir}")

            # 폴더를 비운 프리셋은 블렌드 파일 폴더를 그대로 쓰고, 저장 전이면 오류를 낸다.
            empty = dict(stored)
            empty["export_dir"] = ""
            blend_path = pathlib.Path(temp_dir) / "resolve.blend"
            resolved, error = export_presets.resolve_export_dir(empty, str(blend_path))
            if error:
                fail(f"폴더를 비운 프리셋 경로 계산 실패: {error}")
            if pathlib.Path(resolved) != blend_path.parent:
                fail(f"폴더를 비웠는데 블렌드 파일 폴더가 아닙니다: {resolved}")

            _, error = export_presets.resolve_export_dir(empty, "")
            if not error:
                fail("블렌드 파일이 없고 폴더도 비었는데 오류가 나지 않았습니다.")
        finally:
            export_presets.remove_preset(case.key, preset_name)

    print(f"[CAT Menus Smoke] {case.key.upper()} 지정 폴더 내보내기 통과")


def check_single_file_mode(case):
    """한 파일로 묶어 내보내는 모드를 검증한다."""
    export_presets = export_presets_module()
    preset_name = f"CAT Single {case.key.upper()}"

    with tempfile.TemporaryDirectory() as temp_dir:
        single_dir = pathlib.Path(temp_dir) / "single_export"

        result = resolve_operator(case.add_idname)(
            'EXEC_DEFAULT',
            preset_name=preset_name,
            export_dir=str(single_dir),
            export_mode='SINGLE',
        )
        if result != {"FINISHED"}:
            fail(f"단일 파일 프리셋 등록 실패: {case.key}: {result}")

        try:
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
            first = bpy.context.object
            first.name = "SinglePart"
            bpy.ops.mesh.primitive_cube_add(size=1, location=(2, 0, 0))
            active = bpy.context.object
            active.name = "SingleRoot"
            first.select_set(True)
            active.select_set(True)
            bpy.context.view_layer.objects.active = active

            result = resolve_operator(case.run_idname)('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"단일 파일 내보내기 실패: {case.key}: {result}")

            written = sorted(
                child.name for child in single_dir.iterdir()
                if child.is_file() and child.suffix == case.extension
            )
            if written != [f"SingleRoot{case.extension}"]:
                fail(f"단일 파일 모드 결과가 다릅니다: {case.key}: {written}")
        finally:
            export_presets.remove_preset(case.key, preset_name)

    print(f"[CAT Menus Smoke] {case.key.upper()} 단일 파일 모드 통과")


def check_invalid_object_name(case):
    """파일 이름에 쓸 수 없는 문자가 든 오브젝트도 내보내지는지 검증한다."""
    export_presets = export_presets_module()
    base = importlib.import_module(f"{MODULE_NAME}.operators.export_preset_base")

    # Blender 오브젝트 이름에는 들어갈 수 있지만 Windows 파일 이름에는 못 쓰는 문자들
    for source, expected in (
        ("Body:Arm", "Body_Arm"),
        ("Body/Arm", "Body_Arm"),
        ("Body\\Arm", "Body_Arm"),
        ('Body*?"<>|', "Body______"),
        ("Body ", "Body"),
        ("NUL", "_NUL"),
        ("CON.001", "_CON.001"),
        ("", "untitled"),
        ("Cube.001", "Cube.001"),
    ):
        actual = base.sanitize_file_name(source)
        if actual != expected:
            fail(f"파일 이름 보정 결과가 다릅니다: {source!r} -> {actual!r} != {expected!r}")

    preset_name = f"CAT Invalid Name {case.key.upper()}"

    with tempfile.TemporaryDirectory() as temp_dir:
        export_dir = pathlib.Path(temp_dir) / "invalid_name"
        result = resolve_operator(case.add_idname)(
            'EXEC_DEFAULT',
            preset_name=preset_name,
            export_dir=str(export_dir),
        )
        if result != {"FINISHED"}:
            fail(f"이름 보정 검증용 프리셋 등록 실패: {case.key}: {result}")

        try:
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add(size=1)
            cube = bpy.context.object
            cube.name = "Body:Arm"
            cube.select_set(True)
            bpy.context.view_layer.objects.active = cube
            if cube.name != "Body:Arm":
                fail(f"오브젝트 이름을 설정하지 못했습니다: {cube.name!r}")

            result = resolve_operator(case.run_idname)('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"이름에 금지 문자가 있는 오브젝트 내보내기 실패: {case.key}: {result}")

            # OBJ는 .mtl을 함께 쓰므로 확장자가 맞는 파일만 본다.
            written = sorted(
                child.name for child in export_dir.iterdir()
                if child.suffix == case.extension
            )
            if written != [f"Body_Arm{case.extension}"]:
                fail(f"보정된 이름으로 파일이 생기지 않았습니다: {case.key}: {written}")
        finally:
            export_presets.remove_preset(case.key, preset_name)

    print(f"[CAT Menus Smoke] {case.key.upper()} 파일 이름 보정 통과")


def check_export_failure(case):
    """내보내기가 실패하면 성공으로 보고하지 않고 선택도 복원하는지 검증한다."""
    export_presets = export_presets_module()
    preset_name = f"CAT Failure {case.key.upper()}"

    with tempfile.TemporaryDirectory() as temp_dir:
        export_dir = pathlib.Path(temp_dir) / "failure"
        result = resolve_operator(case.add_idname)(
            'EXEC_DEFAULT',
            preset_name=preset_name,
            export_dir=str(export_dir),
        )
        if result != {"FINISHED"}:
            fail(f"실패 검증용 프리셋 등록 실패: {case.key}: {result}")

        try:
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add(size=1)
            blocked = bpy.context.object
            blocked.name = "BlockedCube"
            bpy.ops.mesh.primitive_cube_add(size=1, location=(2, 0, 0))
            healthy = bpy.context.object
            healthy.name = "HealthyCube"

            # 내보낼 파일 자리에 같은 이름의 폴더를 두면 파일을 쓸 수 없다.
            (export_dir / f"BlockedCube{case.extension}").mkdir(parents=True)

            # 하나만 실패하면 나머지는 내보내고 경고만 남긴다.
            blocked.select_set(True)
            healthy.select_set(True)
            bpy.context.view_layer.objects.active = healthy

            result = resolve_operator(case.run_idname)('EXEC_DEFAULT', preset_name=preset_name)
            if result != {"FINISHED"}:
                fail(f"일부 실패 시 결과가 다릅니다: {case.key}: {result}")
            if not (export_dir / f"HealthyCube{case.extension}").is_file():
                fail(f"정상 오브젝트가 내보내지지 않았습니다: {case.key}")

            # 전부 실패하면 성공으로 보고하지 않고 취소해야 한다.
            bpy.ops.object.select_all(action="DESELECT")
            blocked.select_set(True)
            bpy.context.view_layer.objects.active = blocked

            try:
                result = resolve_operator(case.run_idname)('EXEC_DEFAULT', preset_name=preset_name)
            except RuntimeError:
                pass  # 오류 리포트는 bpy.ops에서 RuntimeError로 올라온다
            else:
                fail(f"내보내기에 실패했는데 취소되지 않았습니다: {case.key}: {result}")

            # 실패해도 실행 전 선택 상태가 남아 있어야 한다.
            if not blocked.select_get():
                fail(f"실패 후 선택 상태가 복원되지 않았습니다: {case.key}")
            if bpy.context.view_layer.objects.active is not blocked:
                fail(f"실패 후 액티브 오브젝트가 복원되지 않았습니다: {case.key}")
        finally:
            export_presets.remove_preset(case.key, preset_name)

    print(f"[CAT Menus Smoke] {case.key.upper()} 내보내기 실패 보고 통과")


class EditLoadHost:
    """ExportPresetEdit._load()에 넘길 연산자 대역."""

    def __init__(self, spec, target_name):
        self.spec = spec
        self.target_name = target_name


def check_preset_edit(case):
    """프리셋 수정(값 불러오기·옵션 변경·이름 바꾸기)을 검증한다."""
    export_presets = export_presets_module()
    base = importlib.import_module(f"{MODULE_NAME}.operators.export_preset_base")
    spec = export_presets.SPECS[case.key]

    origin = f"CAT Edit {case.key.upper()}"
    renamed = f"{origin} Renamed"
    edit_operator = resolve_operator(case.edit_idname)

    try:
        result = resolve_operator(case.add_idname)(
            'EXEC_DEFAULT', preset_name=origin, export_dir="", **case.sample
        )
        if result != {"FINISHED"}:
            fail(f"수정 검증용 프리셋 등록 실패: {case.key}: {result}")

        # 대화창을 열면 저장된 값이 그대로 채워져야 한다.
        host = EditLoadHost(spec, origin)
        base.ExportPresetEdit._load(host, spec.normalize(export_presets.get_preset(case.key, origin)))
        if host.preset_name != origin:
            fail(f"수정 대화창에 프리셋 이름이 채워지지 않았습니다: {host.preset_name!r}")
        for key, expected in case.sample.items():
            actual = getattr(host, key)
            if isinstance(expected, set):
                actual = set(actual)
            if actual != expected:
                fail(f"수정 대화창에 저장값이 채워지지 않았습니다: {key}={actual!r} != {expected!r}")

        # 없는 프리셋을 수정하려 하면 취소되어야 한다.
        try:
            result = edit_operator('EXEC_DEFAULT', target_name="없는 프리셋", preset_name=origin)
        except RuntimeError:
            pass
        else:
            fail(f"없는 프리셋 수정이 취소되지 않았습니다: {case.key}: {result}")

        # 이름과 옵션을 함께 바꾼다.
        changed = dict(case.sample, global_scale=3.0)
        result = edit_operator(
            'EXEC_DEFAULT', target_name=origin, preset_name=renamed, export_dir="", **changed
        )
        if result != {"FINISHED"}:
            fail(f"프리셋 수정 실패: {case.key}: {result}")

        names = export_presets.preset_names(case.key)
        if origin in names:
            fail(f"이름을 바꿨는데 예전 프리셋이 남아 있습니다: {origin}")
        if renamed not in names:
            fail(f"바꾼 이름의 프리셋이 없습니다: {renamed}")

        stored = export_presets.get_preset(case.key, renamed)
        for key, expected in changed.items():
            actual = stored[key]
            if isinstance(expected, set):
                actual = set(actual)
            if actual != expected:
                fail(f"수정한 값이 저장되지 않았습니다: {case.key}.{key}={actual!r} != {expected!r}")

        # 이름을 그대로 두고 옵션만 바꿀 수도 있어야 한다.
        result = edit_operator(
            'EXEC_DEFAULT', target_name=renamed, preset_name=renamed, export_dir="",
            **dict(case.sample, global_scale=4.0)
        )
        if result != {"FINISHED"}:
            fail(f"이름을 유지한 프리셋 수정 실패: {case.key}: {result}")
        if export_presets.get_preset(case.key, renamed)["global_scale"] != 4.0:
            fail(f"이름을 유지한 수정이 저장되지 않았습니다: {case.key}")
    finally:
        export_presets.remove_preset(case.key, origin)
        export_presets.remove_preset(case.key, renamed)

    print(f"[CAT Menus Smoke] {case.key.upper()} 프리셋 수정 통과")


class DrawHost:
    """draw() 함수에 넘길 self 대역. layout과 클래스 속성만 제공한다."""

    def __init__(self, layout, op_idname=None, owner=None):
        self.layout = layout
        self.op_idname = op_idname
        self.owner = owner

    def __getattr__(self, name):
        # 메뉴/연산자 클래스에 정의된 속성은 그대로 넘겨준다.
        owner = self.__dict__.get("owner")
        if owner is not None and hasattr(owner, name):
            return getattr(owner, name)

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
        self.enabled = True

    def _child(self):
        return StubLayout(self.log)

    def row(self, **kwargs):
        return self._child()

    def column(self, **kwargs):
        return self._child()

    def box(self, **kwargs):
        return self._child()

    def panel(self, idname, **kwargs):
        self.log.append(("panel", idname))
        return self._child(), self._child()

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


def resolve_operator(idname):
    """연산자 idname으로 호출 가능한 연산자를 찾는다."""
    prefix, op_name = idname.split(".", 1)
    return getattr(getattr(bpy.ops, prefix), op_name)


def resolve_operator_properties(idname):
    """연산자의 RNA 프로퍼티 전체를 돌려준다."""
    return resolve_operator(idname).get_rna_type().properties


def resolve_operator_property(idname, name):
    """연산자 idname과 프로퍼티 이름으로 RNA 프로퍼티를 찾는다."""
    return resolve_operator_properties(idname).get(name)


def check_menu_draw():
    """메뉴와 프리셋 대화창의 draw() 경로를 UI 없이 실행한다."""
    menu_module = importlib.import_module(f"{MODULE_NAME}.menu")
    export_presets = export_presets_module()

    cases = (
        (menu_module.ExportFBXPresetMenu, EXPORT_CASES[0]),
        (menu_module.ExportOBJPresetMenu, EXPORT_CASES[1]),
    )

    for menu_class, case in cases:
        preset_name = f"CAT Draw {case.key.upper()}"
        spec = export_presets.SPECS[case.key]
        saved, _ = export_presets.add_preset(case.key, preset_name, spec.defaults())
        if not saved:
            fail("draw 검증용 프리셋을 저장하지 못했습니다.")

        try:
            # 프리셋이 있을 때: 실행 항목과 삭제 항목, 프리셋 등록 항목이 모두 나와야 한다.
            log = []
            menu_class.draw(DrawHost(StubLayout(log), owner=menu_class), bpy.context)
            operators = [entry for entry in log if entry[0] == "operator"]
            texts = [entry[2] for entry in operators]
            if preset_name not in texts:
                fail(f"하위 메뉴에 프리셋이 표시되지 않았습니다: {texts}")
            idnames = {entry[1] for entry in operators}
            for expected in (case.run_idname, case.add_idname, case.edit_idname, case.remove_idname):
                if expected not in idnames:
                    fail(f"하위 메뉴에 항목이 없습니다: {expected}")

            # 프리셋 등록 항목 이름은 '프리셋'이어야 한다.
            add_texts = [entry[2] for entry in operators if entry[1] == case.add_idname]
            if add_texts != ["프리셋"]:
                fail(f"프리셋 등록 항목 이름이 다릅니다: {add_texts}")

            # 프리셋이 없을 때: 안내 라벨과 등록 항목만 남아야 한다.
            export_presets.remove_preset(case.key, preset_name)
            log = []
            menu_class.draw(DrawHost(StubLayout(log), owner=menu_class), bpy.context)
            if not any(entry[0] == "label" for entry in log):
                fail("프리셋이 없을 때 안내 라벨이 표시되지 않았습니다.")
            if any(entry[0] == "operator" and entry[1] == case.run_idname for entry in log):
                fail("프리셋이 없는데 내보내기 항목이 표시되었습니다.")

            # 프리셋 등록·수정 대화창 draw 경로
            for idname in (case.add_idname, case.edit_idname):
                log = []
                dialog_class = next(
                    cls for cls in importlib.import_module(MODULE_NAME).CLASSES
                    if getattr(cls, "bl_idname", "") == idname
                )
                dialog_class.draw(DrawHost(StubLayout(log), idname, owner=dialog_class), bpy.context)
                drawn = {entry[1] for entry in log if entry[0] == "prop"}
                missing = ({"preset_name", "export_dir", "export_mode"} | set(spec.option_names())) - drawn
                if missing:
                    fail(f"프리셋 대화창에 빠진 프로퍼티가 있습니다: {idname}: {sorted(missing)}")
        finally:
            export_presets.remove_preset(case.key, preset_name)

    # CAT 메뉴가 Export OBJ / Export FBX를 하위 메뉴로 연결하는지 확인한다.
    log = []
    menu_module.CatMenusMenu.draw(DrawHost(StubLayout(log), owner=menu_module.CatMenusMenu), bpy.context)
    for menu_class, _ in cases:
        if ("menu", menu_class.bl_idname) not in log:
            fail(f"CAT 메뉴에 하위 메뉴가 없습니다: {menu_class.bl_idname}")
    for _, case in cases:
        if any(entry[0] == "operator" and entry[1] == case.run_idname for entry in log):
            fail(f"CAT 메뉴에 연산자가 직접 남아 있습니다: {case.run_idname}")

    print("[CAT Menus Smoke] 메뉴 draw 통과")


def read_manifest():
    import tomllib

    module = importlib.import_module(MODULE_NAME)
    manifest_path = pathlib.Path(module.__file__).resolve().parent / "blender_manifest.toml"
    return tomllib.loads(manifest_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
