import bpy


class MatchName(bpy.types.Operator):
    """데이터 이름을 오브젝트 이름으로 변경합니다."""
    bl_idname = "object.match_name"
    bl_label = "Match name"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        num = 0
            # 전체 메쉬의 임시 이름을 지정 (중복 방지)
        for mesh in bpy.data.meshes:
            mesh.name = str(num)
            num += 1
            # 실제 사용될 이름으로 변경
        for obj in bpy.data.objects:
            obj.data.name = obj.name
                            
        return {'FINISHED'}
