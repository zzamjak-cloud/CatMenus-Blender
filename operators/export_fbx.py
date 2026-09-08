import os

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

from .. import fbx_presets


class ExportFBX(bpy.types.Operator):
    """선택한 오브젝트를 프리셋 설정으로 각각의 FBX 파일로 추출합니다."""
    bl_idname = "object.export_fbx"
    bl_label = "Export FBX"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: StringProperty(
        name="프리셋",
        description="사용할 FBX 내보내기 프리셋 이름",
        default="",
    )

    def execute(self, context):
        # 프리셋 확인
        if not self.preset_name:
            self.report({'ERROR'}, "사용할 프리셋을 선택하세요.")
            return {'CANCELLED'}

        preset = fbx_presets.get_preset(self.preset_name)
        if preset is None:
            self.report({'ERROR'}, f"프리셋을 찾을 수 없습니다: {self.preset_name}")
            return {'CANCELLED'}

        # 프리셋에 폴더가 지정되어 있으면 그 폴더로, 없으면 블렌드 파일 옆 폴더로 내보낸다.
        export_dir, path_error = fbx_presets.resolve_export_dir(preset, bpy.data.filepath)
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

        kwargs = fbx_presets.export_kwargs(preset)
        active_object = context.view_layer.objects.active

        # 오브젝트별로 하나씩만 선택해 개별 파일로 추출한다.
        bpy.ops.object.select_all(action='DESELECT')

        exported = 0
        for obj in selected_objects:
            export_path = os.path.join(export_dir, obj.name + '.fbx')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            bpy.ops.export_scene.fbx(filepath=export_path, use_selection=True, **kwargs)
            exported += 1

            obj.select_set(False)

        # 실행 전 선택 상태를 복원한다.
        for obj in selected_objects:
            obj.select_set(True)
        if active_object is not None:
            context.view_layer.objects.active = active_object

        self.report({'INFO'}, f"'{self.preset_name}' 프리셋으로 {exported}개 FBX를 내보냈습니다: {export_dir}")
        return {'FINISHED'}


class ExportFBXPresetAdd(bpy.types.Operator):
    """새 FBX 내보내기 프리셋을 만들어 로컬에 저장합니다."""
    bl_idname = "object.export_fbx_preset_add"
    bl_label = "+프리셋"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(
        name="프리셋 이름",
        description="하위 메뉴에 표시할 프리셋 이름",
        default="New Preset",
    )
    export_dir: StringProperty(
        name="내보내기 폴더",
        description="FBX를 저장할 폴더. 지정하면 이 폴더로 바로 내보내고, 비우면 아래 폴더 이름을 사용",
        default=fbx_presets.DEFAULT_PRESET["export_dir"],
        subtype='DIR_PATH',
    )
    export_subdir: StringProperty(
        name="폴더 이름",
        description="내보내기 폴더를 비웠을 때 블렌드 파일 옆에 만들 폴더 이름",
        default=fbx_presets.DEFAULT_PRESET["export_subdir"],
    )
    object_types: EnumProperty(
        name="오브젝트 타입",
        description="내보낼 오브젝트 타입",
        items=fbx_presets.OBJECT_TYPE_ITEMS,
        default={'MESH'},
        options={'ENUM_FLAG'},
    )
    use_mesh_modifiers: BoolProperty(
        name="모디파이어 적용",
        description="내보낼 때 모디파이어를 적용",
        default=fbx_presets.DEFAULT_PRESET["use_mesh_modifiers"],
    )
    mesh_smooth_type: EnumProperty(
        name="스무딩",
        description="스무딩 정보를 내보내는 방식",
        items=fbx_presets.MESH_SMOOTH_TYPE_ITEMS,
        default=fbx_presets.DEFAULT_PRESET["mesh_smooth_type"],
    )
    use_triangles: BoolProperty(
        name="삼각형 분할",
        description="면을 삼각형으로 변환해 내보내기",
        default=fbx_presets.DEFAULT_PRESET["use_triangles"],
    )
    use_custom_props: BoolProperty(
        name="커스텀 프로퍼티",
        description="커스텀 프로퍼티를 함께 내보내기",
        default=fbx_presets.DEFAULT_PRESET["use_custom_props"],
    )
    bake_anim: BoolProperty(
        name="애니메이션 베이크",
        description="애니메이션을 베이크해 내보내기",
        default=fbx_presets.DEFAULT_PRESET["bake_anim"],
    )
    global_scale: FloatProperty(
        name="스케일",
        description="전역 스케일",
        default=fbx_presets.DEFAULT_PRESET["global_scale"],
        min=0.001,
        max=1000.0,
    )
    apply_unit_scale: BoolProperty(
        name="유닛 스케일 적용",
        description="씬 유닛 스케일을 적용",
        default=fbx_presets.DEFAULT_PRESET["apply_unit_scale"],
    )
    apply_scale_options: EnumProperty(
        name="스케일 방식",
        description="스케일을 적용하는 방식",
        items=fbx_presets.APPLY_SCALE_OPTIONS_ITEMS,
        default=fbx_presets.DEFAULT_PRESET["apply_scale_options"],
    )
    axis_forward: EnumProperty(
        name="전방 축",
        description="전방으로 사용할 축",
        items=fbx_presets.AXIS_ITEMS,
        default=fbx_presets.DEFAULT_PRESET["axis_forward"],
    )
    axis_up: EnumProperty(
        name="상방 축",
        description="위로 사용할 축",
        items=fbx_presets.AXIS_ITEMS,
        default=fbx_presets.DEFAULT_PRESET["axis_up"],
    )
    path_mode: EnumProperty(
        name="텍스처 경로",
        description="텍스처 경로 처리 방식",
        items=fbx_presets.PATH_MODE_ITEMS,
        default=fbx_presets.DEFAULT_PRESET["path_mode"],
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "preset_name")
        layout.prop(self, "export_dir")
        row = layout.row()
        # 고정 폴더를 지정하면 블렌드 파일 옆 폴더 이름은 쓰이지 않는다.
        row.enabled = not self.export_dir.strip()
        row.prop(self, "export_subdir")

        layout.separator()
        column = layout.column(heading="오브젝트 타입")
        column.use_property_split = False
        column.prop(self, "object_types", expand=True)

        layout.separator()
        layout.prop(self, "use_mesh_modifiers")
        layout.prop(self, "mesh_smooth_type")
        layout.prop(self, "use_triangles")
        layout.prop(self, "use_custom_props")
        layout.prop(self, "bake_anim")

        layout.separator()
        layout.prop(self, "global_scale")
        layout.prop(self, "apply_unit_scale")
        layout.prop(self, "apply_scale_options")
        layout.prop(self, "axis_forward")
        layout.prop(self, "axis_up")
        layout.prop(self, "path_mode")

    def execute(self, context):
        name = self.preset_name.strip()
        if not name:
            self.report({'ERROR'}, "프리셋 이름을 입력하세요.")
            return {'CANCELLED'}

        if not self.object_types:
            self.report({'ERROR'}, "내보낼 오브젝트 타입을 하나 이상 선택하세요.")
            return {'CANCELLED'}

        settings = {
            "export_dir": self.export_dir,
            "export_subdir": self.export_subdir,
            "object_types": sorted(self.object_types),
            "use_mesh_modifiers": self.use_mesh_modifiers,
            "mesh_smooth_type": self.mesh_smooth_type,
            "use_triangles": self.use_triangles,
            "use_custom_props": self.use_custom_props,
            "bake_anim": self.bake_anim,
            "global_scale": self.global_scale,
            "apply_unit_scale": self.apply_unit_scale,
            "apply_scale_options": self.apply_scale_options,
            "axis_forward": self.axis_forward,
            "axis_up": self.axis_up,
            "path_mode": self.path_mode,
        }

        saved, replaced = fbx_presets.add_preset(name, settings)
        if not saved:
            self.report({'ERROR'}, "프리셋을 저장하지 못했습니다. 콘솔 로그를 확인하세요.")
            return {'CANCELLED'}

        if replaced:
            self.report({'WARNING'}, f"같은 이름의 프리셋을 덮어썼습니다: {name}")
        else:
            self.report({'INFO'}, f"프리셋을 저장했습니다: {name}")
        return {'FINISHED'}


class ExportFBXPresetRemove(bpy.types.Operator):
    """저장된 FBX 내보내기 프리셋을 삭제합니다."""
    bl_idname = "object.export_fbx_preset_remove"
    bl_label = "프리셋 삭제"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(
        name="프리셋",
        description="삭제할 프리셋 이름",
        default="",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if not fbx_presets.remove_preset(self.preset_name):
            self.report({'ERROR'}, f"프리셋을 삭제하지 못했습니다: {self.preset_name}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"프리셋을 삭제했습니다: {self.preset_name}")
        return {'FINISHED'}
