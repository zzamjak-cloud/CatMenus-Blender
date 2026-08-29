import os

import bpy
from bpy.props import EnumProperty, FloatProperty


class ExportUV(bpy.types.Operator):
    """선택된 오브젝트들의 UV를 한꺼번에 추출합니다."""
    bl_idname = "object.exportuv"
    bl_label = "Export UV"
    bl_options = {'REGISTER', 'UNDO'}
    
    # texure_size: IntProperty(name="TextureSize", default=256, min=128, max=2048)
    texure_size: EnumProperty(
        name="Texture Size", 
        description="텍스쳐 크기를 지정합니다.",
        items=[('OP1', "256", ""),
               ('OP2', "512", ""),
               ('OP3', "1024", ""),
               ('OP4', "2048", ""),
               ('OP5', "4096", "")],
        default='OP1') # type: ignore
    opacity : FloatProperty(name="Opacity", default=1.0, min=0.0, max=1.0) # type: ignore
    
    # Export UV
    def execute(self, context):
        # Change Texture Size : N x N pixel
        texture_size = self.texure_size
        opacity = self.opacity
        tex_size = 0

        if texture_size == 'OP1':
            tex_size = 256
        elif texture_size == 'OP2':
            tex_size = 512
        elif texture_size == 'OP3':
            tex_size = 1024
        elif texture_size == 'OP4':
            tex_size = 2048
        elif texture_size == 'OP5':
            tex_size = 4096

        # Save directory
        file_path = bpy.data.filepath
        file_dir, file_name = os.path.split(file_path)
        export_dir = os.path.join(file_dir, 'Texture')

        # Check directory
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            print("Create folder")
        else:
            print("Exist folder:", export_dir)

        # Select Object List
        selected_objects = bpy.context.selected_objects

        # Desellect All
        bpy.ops.object.select_all(action='DESELECT')

        for obj in selected_objects:
            # Save File Name
            export_path = os.path.join(export_dir, obj.name + '_UV.png')

            # Export UV
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.export_layout(filepath = export_path, export_all = False, modified = False, mode = 'PNG', size = (tex_size, tex_size),opacity = opacity)
            bpy.ops.object.mode_set(mode="OBJECT")
        
        return {'FINISHED'}
