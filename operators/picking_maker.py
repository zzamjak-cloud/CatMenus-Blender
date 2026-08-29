import bpy
from bpy.props import FloatProperty

from ..utils import check_collection_exist, check_mesh_exist


class PickingMaker(bpy.types.Operator):
    """Picking Collision을 생성합니다."""
    bl_idname = "object.picking"
    bl_label = "Picking maker"
    bl_options = {'REGISTER', 'UNDO'}

    strength : FloatProperty(name="Scale", default=0.25, min=0, max=0.5) # type: ignore
    
    def execute(self, context):
        strength = self.strength
            # 선택된 오브젝트 리스트
        selected_objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        # 동일한 이름의 'Picking' 컬렉션이 존재 여부
        check_collection_exist('Picking')
        target_collection = bpy.data.collections.get('Picking')

        # 이름에 'Collision'이 포함된 것만 추출
        col_objs = []
        for obj in selected_objects:
            if (obj.name.endswith('Collision')):
                col_objs.append(obj)

            # Picking Collision 메쉬 생성
        for obj in col_objs:
                # Picking 메쉬 중복 체크 후 제거
            picking_object_name = obj.name.replace("Collision", "Picking")
            check_mesh_exist(picking_object_name)

                # Picking 오브젝트 신규 생성 및 설정
            picking_object = obj.copy()
            picking_object.data = obj.data.copy()
            picking_object.name = picking_object_name
            picking_object.data.name = picking_object_name
            picking_object.location = obj.location
            
                # 생성된 Picking 오브젝트를 컬렉션에 링크
            bpy.context.collection.objects.link(picking_object)
            
                # Displace 모디파이어 설정
            mod = picking_object.modifiers.new('Displace', type='DISPLACE')
            mod.strength = strength
            bpy.ops.object.modifier_apply(modifier="Displace")
            bpy.ops.object.select_all(action='DESELECT')

            # 컬렉션 이동
            picking_object.users_collection[0].objects.unlink(picking_object)
            target_collection.objects.link(picking_object)
                    
        return {'FINISHED'}
