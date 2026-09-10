import os

import bpy


class CleanSetting(bpy.types.Operator):
    """불필요한 Image와 Material을 제거하고 새로 생성합니다."""
    bl_idname = "object.clean_settings"
    bl_label = "Clean Setting"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        imgDir = os.path.dirname(bpy.data.filepath) + "/Texture/"

        # 모든 머티리얼 데이터 제거
        for mat in bpy.data.materials:
            bpy.data.materials.remove(mat)
            
        # 모든 이미지 데이터 제거
        for img in bpy.data.images:
            bpy.data.images.remove(img)
        
        for obj in bpy.data.objects:

            if 'Collision' not in obj.name:
                name = obj.name    # 오브젝트 이름
                
                # Clear all material slot of object
                obj.data.materials.clear()
                
                # Assign material
                mat = bpy.data.materials.new(name)
                mat.use_nodes = True
                bsdf = mat.node_tree.nodes["Principled BSDF"]
                texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                texImage.image = bpy.data.images.load(imgDir + name + ".png")
                mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                mat.node_tree.nodes["Principled BSDF"].inputs[12].default_value = 0    # Specular value = '0'
                
                obj.data.materials.append(mat)    # Assign material to material slot
            
        return {'FINISHED'}
