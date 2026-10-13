import bpy


class JPLayout(bpy.types.Operator):
    """자주 쓰는 뷰포트·편집 설정 프리셋을 한 번에 적용합니다."""
    bl_idname = "view3d.jp_layout"
    bl_label = "JP Layout"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 열린 모든 창의 3D 뷰포트에 동일하게 적용한다.
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        self.apply_view(space)

        # Auto Merge·Snapping은 씬 단위 설정이라 모드와 무관하게 Edit 모드에도 반영된다.
        tool_settings = context.scene.tool_settings
        tool_settings.use_mesh_automerge = True
        tool_settings.use_snap = True
        tool_settings.snap_elements = {'VERTEX'}

        return {'FINISHED'}

    @staticmethod
    def apply_view(space):
        shading = space.shading
        shading.type = 'SOLID'
        shading.light = 'FLAT'
        shading.wireframe_color_type = 'THEME'
        shading.color_type = 'TEXTURE'

        overlay = space.overlay
        overlay.show_overlays = True
        overlay.show_stats = True
        overlay.show_face_orientation = True
