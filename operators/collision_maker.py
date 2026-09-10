import bpy
from bpy.props import FloatProperty
from mathutils import Matrix, Vector

from ..utils import check_collection_exist, check_mesh_exist


def world_bounds(obj):
    """오브젝트의 월드 공간 바운딩 박스 중심과 크기를 구한다.

    Args:
        obj: 대상 오브젝트

    Returns:
        (중심 좌표 Vector, 크기 Vector) 튜플
    """
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    min_corner = Vector((
        min(corner.x for corner in corners),
        min(corner.y for corner in corners),
        min(corner.z for corner in corners),
    ))
    max_corner = Vector((
        max(corner.x for corner in corners),
        max(corner.y for corner in corners),
        max(corner.z for corner in corners),
    ))

    return (min_corner + max_corner) * 0.5, max_corner - min_corner


class CollisionMaker(bpy.types.Operator):
    """Collision Cube를 오브젝트 크기에 맞게 생성합니다."""
    bl_idname = "object.collision_maker"
    bl_label = "Collision maker"
    bl_options = {'REGISTER', 'UNDO'}

    # 충돌 메시의 크기 가중치
    scale: FloatProperty(name="Scale", default=0.1, min=0.01, max=0.2) # type: ignore

    def execute(self, context):
        padding = self.scale
        # 선택된 오브젝트 리스트
        selected_objects = list(context.selected_objects)
        bpy.ops.object.select_all(action='DESELECT')

        # 동일한 이름의 'Collision' 컬렉션이 존재 여부
        check_collection_exist('Collision')
        target_collection = bpy.data.collections.get('Collision')

        objs = [obj for obj in selected_objects if not obj.name.endswith('Collision')]

        for obj in objs:

            collision_name = obj.name + "_Collision"
            # 동일한 이름의 Collision 메쉬가 존재하는지 체크 후 제거
            check_mesh_exist(collision_name)

            # 원본의 실제 형상 범위(월드 바운딩 박스)와 pivot 위치를 따로 구한다
            bounds_center, bounds_size = world_bounds(obj)
            pivot = obj.matrix_world.translation.copy()

            # 오브젝트 pivot 위치에 Collision Cube 생성 후 WIRE 모드로 변환
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=pivot)
            collision_object = context.active_object
            collision_object.scale = (
                bounds_size.x + padding,
                bounds_size.y + padding,
                bounds_size.z + padding,
            )
            collision_object.name = collision_name
            collision_object.data.name = collision_name
            collision_object.display_type = 'WIRE'

            # Apply Scale
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            # pivot 은 원본과 같은 자리에 두고 메시만 형상 중심으로 옮긴다
            offset = bounds_center - pivot
            if offset.length_squared > 0.0:
                collision_object.data.transform(Matrix.Translation(offset))
                collision_object.data.update()

            bpy.ops.object.select_all(action='DESELECT')

            # 컬렉션 이동
            collision_object.users_collection[0].objects.unlink(collision_object)
            target_collection.objects.link(collision_object)

        return {'FINISHED'}
