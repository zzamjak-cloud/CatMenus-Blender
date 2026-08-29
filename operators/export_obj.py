import os

import bpy


class ExportOBJ(bpy.types.Operator):
    """Obj파일을 한꺼번에 추출합니다."""
    bl_idname = "object.export_obj"
    bl_label = "Export OBJ"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Save directory
        file_path = bpy.data.filepath
        file_dir, file_name = os.path.split(file_path)
        export_dir = os.path.join(file_dir, 'Obj')

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
            export_path = os.path.join(export_dir, obj.name + '.obj')
            print(export_path)
            # Export Obj
            obj.select_set(True)
            bpy.ops.wm.obj_export(filepath=export_path, export_selected_objects=True)
            bpy.ops.object.select_all(action='DESELECT')
            
        return {'FINISHED'}
