import bpy


class JPLayout(bpy.types.Operator):
    """자주 쓰는 뷰포트·편집 설정 프리셋을 한 번에 적용하고 선택한 오브젝트를 Isolate 합니다."""
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
        # 스내핑은 Ctrl을 누른 동안만 쓰므로 대상(Vertex)만 고르고 상시 활성화는 끈다.
        tool_settings = context.scene.tool_settings
        tool_settings.use_mesh_automerge = True
        tool_settings.use_snap = False
        tool_settings.snap_elements = {'VERTEX'}

        self.isolate_selected(context)
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
        overlay.show_wireframes = True

    def isolate_selected(self, context):
        """메뉴를 연 3D 뷰포트에서 선택한 오브젝트만 Local View(Isolate)로 보여 준다."""
        if not context.selected_objects:
            self.report({'INFO'}, "선택한 오브젝트가 없어 Isolate는 건너뜁니다.")
            return

        target = self.find_view3d(context)
        if target is None:
            return
        window, area, region = target

        with context.temp_override(window=window, area=area, region=region):
            # 이미 Isolate 중이면 먼저 빠져나와 현재 선택으로 다시 들어간다.
            if area.spaces.active.local_view:
                bpy.ops.view3d.localview(frame_selected=False)
            bpy.ops.view3d.localview(frame_selected=True)

    @staticmethod
    def find_view3d(context):
        """메뉴를 연 3D 뷰포트를 우선하고, 없으면 처음 찾은 3D 뷰포트를 돌려준다."""
        candidates = []
        if context.area is not None and context.area.type == 'VIEW_3D':
            candidates.append((context.window, context.area))
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    candidates.append((window, area))

        for window, area in candidates:
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region is not None:
                return window, area, region
        return None
