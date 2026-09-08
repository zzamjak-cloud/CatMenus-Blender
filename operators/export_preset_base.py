"""FBX/OBJ 프리셋 내보내기 연산자의 공통 구현.

세 가지 연산자(내보내기 실행 / 프리셋 등록 / 프리셋 삭제)를 믹스인으로 두고,
내보내기 종류별 모듈에서 `spec`만 지정해 상속한다. 대화창에 표시할 내보내기
옵션 프로퍼티는 등록 직전에 `export_presets.apply_dialog_properties()`가
Blender 내보내기 연산자 RNA에서 복제해 붙인다.
"""

import os

import bpy
from bpy.props import EnumProperty, StringProperty

from .. import export_presets


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

        if settings[export_presets.EXPORT_MODE_KEY] == 'SINGLE':
            # 아마추어와 스킨 메시처럼 한 파일에 함께 있어야 하는 경우를 위한 모드.
            base_name = self._single_file_name(selected_objects, active_object)
            export_path = os.path.join(export_dir, base_name + spec.extension)
            export_operator(filepath=export_path, **kwargs)
            exported = 1
        else:
            # 오브젝트별로 하나씩만 선택해 개별 파일로 추출한다.
            bpy.ops.object.select_all(action='DESELECT')

            exported = 0
            for obj in selected_objects:
                export_path = os.path.join(export_dir, obj.name + spec.extension)
                obj.select_set(True)
                context.view_layer.objects.active = obj

                export_operator(filepath=export_path, **kwargs)
                exported += 1

                obj.select_set(False)

            # 실행 전 선택 상태를 복원한다.
            for obj in selected_objects:
                obj.select_set(True)
            if active_object is not None:
                context.view_layer.objects.active = active_object

        self.report(
            {'INFO'},
            f"'{self.preset_name}' 프리셋으로 {exported}개 파일을 내보냈습니다: {export_dir}",
        )
        return {'FINISHED'}

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


class ExportPresetAdd:
    """내보내기 프리셋을 만들어 로컬에 저장하는 연산자 공통 구현."""

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

    def invoke(self, context, event):
        if not self.spec.is_available():
            self.report({'ERROR'}, f"내보내기 연산자를 쓸 수 없습니다: {self.spec.op_path}")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "preset_name")
        layout.prop(self, "export_dir")
        layout.prop(self, "export_mode")
        layout.separator()

        export_presets.draw_options(layout, self, self.spec)

    def execute(self, context):
        spec = self.spec

        name = self.preset_name.strip()
        if not name:
            self.report({'ERROR'}, "프리셋 이름을 입력하세요.")
            return {'CANCELLED'}

        if not spec.is_available():
            self.report({'ERROR'}, f"내보내기 연산자를 쓸 수 없습니다: {spec.op_path}")
            return {'CANCELLED'}

        settings = export_presets.collect_settings(spec, self)

        # 다중 선택 항목을 비운 채로 저장하면 내보내기가 실패하므로 미리 막는다.
        for key, value in settings.items():
            if isinstance(value, list) and not value:
                self.report({'ERROR'}, f"'{key}' 항목을 하나 이상 선택하세요.")
                return {'CANCELLED'}

        saved, replaced = export_presets.add_preset(spec.key, name, settings)
        if not saved:
            self.report({'ERROR'}, "프리셋을 저장하지 못했습니다. 콘솔 로그를 확인하세요.")
            return {'CANCELLED'}

        if replaced:
            self.report({'WARNING'}, f"같은 이름의 프리셋을 덮어썼습니다: {name}")
        else:
            self.report({'INFO'}, f"프리셋을 저장했습니다: {name}")
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
