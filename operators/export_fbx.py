import os

import bpy


class ExportFBX(bpy.types.Operator):
    """FBX파일을 한꺼번에 추출합니다."""
    bl_idname = "object.export_fbx"
    bl_label = "Export FBX"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        # Save directory
        file_path = bpy.data.filepath
        file_dir, file_name = os.path.split(file_path)
        export_dir = os.path.join(file_dir, 'FBX')

        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        else:
            print("폴더가 이미 존재합니다:", export_dir)

        # Select Object List
        selObj = bpy.context.selected_objects

        # Desellect All
        bpy.ops.object.select_all(action='DESELECT')

        for obj in selObj:
            # Save File Name
            export_path = os.path.join(export_dir, obj.name + '.fbx')
            print(export_path)
            # Export Obj
            obj.select_set(True)
        #    bpy.ops.wm.obj_export(filepath=export_path, export_selected_objects=True)
            
            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=True,
                object_types={'MESH'},  # 내보낼 오브젝트 타입 설정
                use_mesh_modifiers=True,
                mesh_smooth_type='FACE',
                bake_anim=False
            )
            
            bpy.ops.object.select_all(action='DESELECT')
        
        return {'FINISHED'}
