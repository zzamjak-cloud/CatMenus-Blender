import bpy


def _is_renamable(datablock):
    """데이터블록의 이름을 이 파일에서 변경할 수 있는지 판단한다.

    - is_editable: 링크된 데이터는 False, 라이브러리 오버라이드는 로컬 복사본이므로 True
    - is_embedded_data: 마스터 컬렉션이나 내장 노드트리처럼 이름을 가질 수 없는 데이터
    """
    if datablock is None:
        return False
    if getattr(datablock, "is_embedded_data", False):
        return False
    # Blender 4.0+ 에서 제공. 없으면 library 유무로 대체 판정
    is_editable = getattr(datablock, "is_editable", None)
    if is_editable is not None:
        return bool(is_editable)
    return getattr(datablock, "library", None) is None


class MatchName(bpy.types.Operator):
    """데이터 이름을 오브젝트 이름으로 변경합니다."""
    bl_idname = "object.match_name"
    bl_label = "Match name"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 이름 변경 대상 오브젝트: 선택된 것이 있으면 선택분만, 없으면 전체
        objects = list(context.selected_objects) or list(bpy.data.objects)

        # 이름 변경이 가능한 데이터블록만 수집 (링크 데이터 제외)
        targets = []
        seen = set()
        skipped = 0
        for obj in objects:
            data = obj.data
            if data is None:
                continue
            if not _is_renamable(data):
                skipped += 1
                continue
            key = data.as_pointer()
            if key in seen:
                continue
            seen.add(key)
            targets.append((data, obj.name))

        # 이름 충돌을 피하기 위해 임시 이름으로 먼저 변경
        renamed = []
        for index, (data, name) in enumerate(targets):
            try:
                data.name = "__cat_match_tmp_%d__" % index
            except AttributeError:
                # is_editable 로 걸러지지 않은 예외적인 read-only 데이터
                skipped += 1
                continue
            renamed.append((data, name))

        # 실제 사용될 이름으로 변경
        for data, name in renamed:
            data.name = name

        if skipped:
            self.report({'WARNING'},
                        "%d개의 링크된 데이터는 이름을 변경할 수 없어 건너뛰었습니다." % skipped)
        else:
            self.report({'INFO'}, "%d개의 데이터 이름을 변경했습니다." % len(renamed))
        return {'FINISHED'}
