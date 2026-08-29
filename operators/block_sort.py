import bpy
from bpy.props import IntProperty


class BlockSort(bpy.types.Operator):
    """선택된 블럭들을 그리드 단위로 정렬시킵니다."""
    bl_idname = "object.block_sort"
    bl_label = "Block sort"
    bl_options = {'REGISTER', 'UNDO'}

    column: IntProperty(name="열 개수 :", default=10, min=1, max=100) # type: ignore
    
    def execute(self, context):
        # 정렬 시작 포인트
        xPos, yPos, zPos = 0.5, 0.5, 0.5

        objs = context.selected_objects
        
        # 정렬 키 함수 정의
        def sort_key(obj):
            name = obj.name
            parts = name.split('_')
            base_name = parts[0]
            has_underscore = '_' in name
            suffix = parts[1] if has_underscore else 'zzzz'  # '_'가 없으면 가장 뒤로
            return (base_name, suffix, name)

        objs.sort(key=sort_key)

        for i, obj in enumerate(objs):
            obj.location = (xPos, yPos, zPos)
            
            # 다음 위치 계산
            xPos += 1.0
            if (i + 1) % self.column == 0:  # 열 개수에 도달하면 다음 행으로
                xPos = 0.5
                yPos -= 1.0
                zPos -= 1.0  # z축 이동

        return {'FINISHED'}
