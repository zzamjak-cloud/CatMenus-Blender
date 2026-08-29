import bpy
from bpy.props import FloatProperty

from ..utils import check_collection_exist, check_mesh_exist


class CollisionMaker(bpy.types.Operator):
    """Collision Cube를 오브젝트 크기에 맞게 생성합니다."""
    bl_idname = "object.collision_maker"
    bl_label = "Collision maker"
    bl_options = {'REGISTER', 'UNDO'}
        # 충돌 메시의 크기 가중치
    scale: FloatProperty(name="Scale", default=0.1, min=0.01, max=0.2) # type: ignore
    
    def execute(self, context):
        scale = self.scale
            # 선택된 오브젝트 리스트
        selected_objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        # 동일한 이름의 'Collision' 컬렉션이 존재 여부
        check_collection_exist('Collision')
        target_collection = bpy.data.collections.get('Collision')
        
        objs = []

        for obj in selected_objects:
            if (obj.name.endswith('Collision')) or (obj.name.endswith('Picking')):
                continue
            else:
                objs.append(obj)

        for obj in objs:

            collision_name = obj.name + "_Collision"
            # 동일한 이름의 Collision 메쉬가 존재하는지 체크 후 제거
            check_mesh_exist(collision_name)
            cube_size = obj.dimensions
            # 오브젝트 위치에 Collision Cube 생성 후 WIRE 모드로 변환
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            collision_object = bpy.context.active_object
            collision_object.location = obj.location
            collision_object.scale = (cube_size[0] + scale, cube_size[1] + scale, cube_size[2] + scale)
            collision_object.name = collision_name
            collision_object.data.name = collision_name
            bpy.context.object.display_type = 'WIRE'
            
            # Applay Scale
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bpy.ops.object.select_all(action='DESELECT')

            # 컬렉션 이동
            collision_object.users_collection[0].objects.unlink(collision_object)
            target_collection.objects.link(collision_object)

        return {'FINISHED'}
