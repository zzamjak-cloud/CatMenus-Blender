"""FBX/OBJ 프리셋 내보내기 연산자의 공통 구현.

네 가지 연산자(내보내기 실행 / 프리셋 등록 / 프리셋 수정 / 프리셋 삭제)를 믹스인으로
두고, 내보내기 종류별 모듈에서 `spec`만 지정해 상속한다. 대화창에 표시할 내보내기
옵션 프로퍼티는 등록 직전에 `export_presets.apply_dialog_properties()`가
Blender 내보내기 연산자 RNA에서 복제해 붙인다.
"""

import os

import bpy
from bpy.props import EnumProperty, StringProperty

from .. import export_presets


# Windows 파일 이름에 쓸 수 없는 문자. Blender 오브젝트 이름에는 들어갈 수 있어서
# 그대로 파일 이름으로 쓰면 내보내기가 실패하거나(`/` `*` `?`) 엉뚱한 파일이 생긴다(`:`).
_INVALID_FILE_CHARS = '\\/:*?"<>|'

# Windows 예약 장치 이름. 이 이름으로는 파일을 만들 수 없다.
_RESERVED_FILE_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{index}" for index in range(1, 10)]
    + [f"LPT{index}" for index in range(1, 10)]
)

# 리포트 한 줄에 나열할 최대 항목 수
_REPORT_LIMIT = 3


def sanitize_file_name(name):
    """오브젝트 이름을 파일 이름으로 쓸 수 있게 고친다.

    금지 문자와 제어 문자는 `_`로 바꾸고, Windows가 무시하는 이름 끝 공백은 없앤다.
    """
    cleaned = "".join(
        "_" if character in _INVALID_FILE_CHARS or character < " " else character
        for character in name
    )
    cleaned = cleaned.rstrip(" ")

    if not cleaned:
        return "untitled"

    # `CON`, `NUL.001`처럼 예약 이름으로 시작하면 파일을 만들 수 없다.
    if cleaned.split(".", 1)[0].upper() in _RESERVED_FILE_NAMES:
        cleaned = f"_{cleaned}"

    return cleaned


# Blender가 감싸서 올려주는 예외 문자열에서 원인과 상관없는 줄
_ERROR_NOISE_PREFIXES = ("Traceback", "File ", "Location:", "Error: Python:", "~", "^")


def _error_line(error):
    """예외 메시지에서 리포트에 쓸 원인 한 줄만 뽑는다.

    bpy.ops 예외에는 파이썬 트레이스백과 `Location:` 줄까지 들어 있어 그대로
    보여주면 정작 원인이 묻힌다.
    """
    lines = [line.strip() for line in str(error).splitlines() if line.strip()]
    causes = [line for line in lines if not line.startswith(_ERROR_NOISE_PREFIXES)]
    if causes:
        return causes[-1]
    return lines[-1] if lines else type(error).__name__


class ExportPresetRun:
    """선택한 오브젝트를 프리셋 설정으로 내보내는 연산자 공통 구현."""

    bl_options = {'REGISTER', 'UNDO'}

    # 상속 클래스에서 지정한다.
    spec = None

    preset_name: StringProperty(
        name="Preset",
        description="Name of the export preset to use",
        default="",
    )

    def execute(self, context):
        spec = self.spec

        if not spec.is_available():
            self.report({'ERROR'}, f"내보내기 연산자를 쓸 수 없습니다: {spec.op_path}")
            return {'CANCELLED'}

        if not self.preset_name:
            self.report({'ERROR'}, "사용할 프리셋을 선택하세요.")
            return {'CANCELLED'}

        preset = export_presets.get_preset(spec.key, self.preset_name)
        if preset is None:
            self.report({'ERROR'}, f"프리셋을 찾을 수 없습니다: {self.preset_name}")
            return {'CANCELLED'}

        settings = spec.normalize(preset)

        # 프리셋에 폴더가 지정되어 있으면 그 폴더로, 없으면 블렌드 파일이 있는 폴더로 내보낸다.
        export_dir, path_error = export_presets.resolve_export_dir(settings, bpy.data.filepath)
        if path_error:
            self.report({'ERROR'}, path_error)
            return {'CANCELLED'}

        selected_objects = list(context.selected_objects)
        if not selected_objects:
            self.report({'ERROR'}, "내보낼 오브젝트를 선택하세요.")
            return {'CANCELLED'}

        try:
            os.makedirs(export_dir, exist_ok=True)
        except OSError as error:
            self.report({'ERROR'}, f"내보내기 폴더를 만들지 못했습니다: {error}")
            return {'CANCELLED'}

        kwargs = spec.export_kwargs(settings)
        active_object = context.view_layer.objects.active
        export_operator = self._export_operator()

        renamed = []   # 파일 이름을 고친 오브젝트 `(원래 이름, 파일 이름)`
        failures = []  # 내보내지 못한 오브젝트 `(이름, 이유)`
        exported = 0

        if settings[export_presets.EXPORT_MODE_KEY] == 'SINGLE':
            # 아마추어와 스킨 메시처럼 한 파일에 함께 있어야 하는 경우를 위한 모드.
            source_name = self._single_file_name(selected_objects, active_object)
            export_path = self._export_path(export_dir, source_name, spec.extension, renamed)
            if self._write(export_operator, export_path, kwargs, source_name, failures):
                exported = 1
        else:
            # 오브젝트별로 하나씩만 선택해 개별 파일로 추출한다.
            bpy.ops.object.select_all(action='DESELECT')

            try:
                for obj in selected_objects:
                    export_path = self._export_path(export_dir, obj.name, spec.extension, renamed)
                    obj.select_set(True)
                    context.view_layer.objects.active = obj

                    if self._write(export_operator, export_path, kwargs, obj.name, failures):
                        exported += 1

                    obj.select_set(False)
            finally:
                # 중간에 실패하더라도 실행 전 선택 상태를 반드시 복원한다.
                for obj in selected_objects:
                    obj.select_set(True)
                if active_object is not None:
                    context.view_layer.objects.active = active_object

        return self._report_result(exported, renamed, failures, export_dir)

    def _report_result(self, exported, renamed, failures, export_dir):
        """내보내기 결과를 사용자에게 알리고 연산자 반환값을 정한다."""
        if renamed:
            self.report(
                {'WARNING'},
                "파일 이름에 쓸 수 없는 문자를 바꿨습니다: "
                + self._summary(f"{source} → {cleaned}" for source, cleaned in renamed),
            )

        if failures:
            detail = self._summary(f"{name}({reason})" for name, reason in failures)
            if exported == 0:
                self.report({'ERROR'}, f"내보내기에 실패했습니다: {detail}")
                return {'CANCELLED'}
            self.report({'WARNING'}, f"{len(failures)}개를 내보내지 못했습니다: {detail}")

        self.report(
            {'INFO'},
            f"'{self.preset_name}' 프리셋으로 {exported}개 파일을 내보냈습니다: {export_dir}",
        )
        return {'FINISHED'}

    @staticmethod
    def _summary(entries):
        """리포트 한 줄에 담을 수 있는 만큼만 묶는다."""
        items = list(entries)
        shown = ", ".join(items[:_REPORT_LIMIT])
        if len(items) > _REPORT_LIMIT:
            shown += f" 외 {len(items) - _REPORT_LIMIT}개"
        return shown

    @staticmethod
    def _export_path(export_dir, source_name, extension, renamed):
        """오브젝트 이름으로 실제 내보낼 파일 경로를 만든다."""
        file_name = sanitize_file_name(source_name)
        if file_name != source_name:
            renamed.append((source_name, file_name))
        return os.path.join(export_dir, file_name + extension)

    @staticmethod
    def _write(export_operator, export_path, kwargs, source_name, failures):
        """내보내기 연산자를 호출하고 파일이 실제로 만들어졌는지 확인한다."""
        try:
            result = export_operator(filepath=export_path, **kwargs)
        except (RuntimeError, OSError) as error:
            failures.append((source_name, _error_line(error)))
            return False

        if 'FINISHED' not in result:
            failures.append((source_name, "내보내기 연산자가 취소되었습니다"))
            return False

        if not os.path.isfile(export_path):
            failures.append((source_name, "파일이 만들어지지 않았습니다"))
            return False

        return True

    def _export_operator(self):
        """프리셋이 가리키는 Blender 내보내기 연산자를 돌려준다."""
        module_name, op_name = self.spec.op_path.split(".", 1)
        return getattr(getattr(bpy.ops, module_name), op_name)

    @staticmethod
    def _single_file_name(selected_objects, active_object):
        """한 파일로 내보낼 때 쓸 파일 이름을 정한다."""
        if active_object is not None and active_object in selected_objects:
            return active_object.name
        return selected_objects[0].name


class ExportPresetDialog:
    """프리셋 등록·수정 대화창의 공통 구현.

    CAT 전용 항목(이름·폴더·모드)만 여기에 두고, 내보내기 옵션 프로퍼티는
    `export_presets.apply_dialog_properties()`가 등록 직전에 붙인다.
    """

    bl_options = {'REGISTER'}

    # 상속 클래스에서 지정한다.
    spec = None

    preset_name: StringProperty(
        name="Preset Name",
        description="Name shown in the preset submenu",
        default="New Preset",
    )
    export_dir: StringProperty(
        name="Export Folder",
        description="Folder to write files into. Leave empty to use the folder of the current blend file",
        default="",
        subtype='DIR_PATH',
    )
    export_mode: EnumProperty(
        name="Export Mode",
        description="How selected objects are split across files",
        items=export_presets.EXPORT_MODE_ITEMS,
        default=export_presets.DEFAULT_EXPORT_MODE,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "preset_name")
        layout.prop(self, "export_dir")
        layout.prop(self, "export_mode")
        layout.separator()

        export_presets.draw_options(layout, self, self.spec)

    def _validated_settings(self):
        """대화창 입력을 검증해 저장할 설정으로 만든다. 문제가 있으면 None."""
        spec = self.spec

        if not self.preset_name.strip():
            self.report({'ERROR'}, "프리셋 이름을 입력하세요.")
            return None

        if not spec.is_available():
            self.report({'ERROR'}, f"내보내기 연산자를 쓸 수 없습니다: {spec.op_path}")
            return None

        settings = export_presets.collect_settings(spec, self)

        # 다중 선택 항목을 비운 채로 저장하면 내보내기가 실패하므로 미리 막는다.
        for key, value in settings.items():
            if isinstance(value, list) and not value:
                self.report({'ERROR'}, f"'{key}' 항목을 하나 이상 선택하세요.")
                return None

        return settings


class ExportPresetAdd(ExportPresetDialog):
    """내보내기 프리셋을 만들어 로컬에 저장하는 연산자 공통 구현."""

    def invoke(self, context, event):
        if not self.spec.is_available():
            self.report({'ERROR'}, f"내보내기 연산자를 쓸 수 없습니다: {self.spec.op_path}")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=420)

    def execute(self, context):
        settings = self._validated_settings()
        if settings is None:
            return {'CANCELLED'}

        name = self.preset_name.strip()
        saved, replaced = export_presets.add_preset(self.spec.key, name, settings)
        if not saved:
            self.report({'ERROR'}, "프리셋을 저장하지 못했습니다. 콘솔 로그를 확인하세요.")
            return {'CANCELLED'}

        if replaced:
            self.report({'WARNING'}, f"같은 이름의 프리셋을 덮어썼습니다: {name}")
        else:
            self.report({'INFO'}, f"프리셋을 저장했습니다: {name}")
        return {'FINISHED'}


class ExportPresetEdit(ExportPresetDialog):
    """저장된 내보내기 프리셋을 불러와 이름과 옵션을 고치는 연산자 공통 구현.

    `target_name`이 고칠 프리셋을 가리킨다. 대화창에서 이름을 바꾸면 원래 프리셋을
    지우고 새 이름으로 저장하므로 이름 변경이 곧 이름 바꾸기가 된다.
    """

    # 고칠 프리셋의 원래 이름. 메뉴에서 넘겨주고 대화창에는 그리지 않는다.
    target_name: StringProperty(
        name="Target Preset",
        description="Name of the export preset to edit",
        default="",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        spec = self.spec

        if not spec.is_available():
            self.report({'ERROR'}, f"내보내기 연산자를 쓸 수 없습니다: {spec.op_path}")
            return {'CANCELLED'}

        preset = export_presets.get_preset(spec.key, self.target_name)
        if preset is None:
            self.report({'ERROR'}, f"프리셋을 찾을 수 없습니다: {self.target_name}")
            return {'CANCELLED'}

        self._load(spec.normalize(preset))
        return context.window_manager.invoke_props_dialog(self, width=420)

    def _load(self, settings):
        """저장된 설정을 대화창 프로퍼티에 채운다."""
        spec = self.spec

        self.preset_name = self.target_name
        self.export_dir = settings[export_presets.EXPORT_DIR_KEY]
        self.export_mode = settings[export_presets.EXPORT_MODE_KEY]

        properties = spec.rna_properties()
        for name in spec.option_names():
            value = settings[name]
            prop = properties[name]
            if prop.type == 'ENUM' and prop.is_enum_flag:
                value = set(value)
            try:
                setattr(self, name, value)
            except (AttributeError, TypeError, ValueError) as error:
                # 이 Blender 버전이 받아들이지 않는 값은 기본값으로 남겨 둔다.
                print(f"[CAT Menus] 프리셋 값을 대화창에 채우지 못했습니다: {name}: {error}")

    def execute(self, context):
        spec = self.spec

        settings = self._validated_settings()
        if settings is None:
            return {'CANCELLED'}

        if export_presets.get_preset(spec.key, self.target_name) is None:
            self.report({'ERROR'}, f"프리셋을 찾을 수 없습니다: {self.target_name}")
            return {'CANCELLED'}

        name = self.preset_name.strip()
        renamed = name != self.target_name
        overwritten = renamed and export_presets.get_preset(spec.key, name) is not None

        saved, _ = export_presets.add_preset(spec.key, name, settings)
        if not saved:
            self.report({'ERROR'}, "프리셋을 저장하지 못했습니다. 콘솔 로그를 확인하세요.")
            return {'CANCELLED'}

        if renamed:
            export_presets.remove_preset(spec.key, self.target_name)

        if overwritten:
            self.report({'WARNING'}, f"같은 이름의 프리셋을 덮어썼습니다: {self.target_name} → {name}")
        elif renamed:
            self.report({'INFO'}, f"프리셋 이름을 바꿨습니다: {self.target_name} → {name}")
        else:
            self.report({'INFO'}, f"프리셋을 수정했습니다: {name}")
        return {'FINISHED'}


class ExportPresetRemove:
    """저장된 내보내기 프리셋을 삭제하는 연산자 공통 구현."""

    bl_options = {'REGISTER'}

    # 상속 클래스에서 지정한다.
    spec = None

    preset_name: StringProperty(
        name="Preset",
        description="Name of the export preset to delete",
        default="",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if not export_presets.remove_preset(self.spec.key, self.preset_name):
            self.report({'ERROR'}, f"프리셋을 삭제하지 못했습니다: {self.preset_name}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"프리셋을 삭제했습니다: {self.preset_name}")
        return {'FINISHED'}
