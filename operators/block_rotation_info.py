import math

import bpy


class BlockRotationInfo(bpy.types.Operator):
    """블럭의 Rotation 정보를 txt 파일로 추출"""
    bl_idname = "object.block_rotation_info"
    bl_label = "Block Rotation Info"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        listName = []
        listVal = []
        cntObj = len(bpy.data.objects)
        data = ''

        # (블렌더파일명)_Rotation.txt
        save_path = bpy.data.filepath.replace('.blend', '_Rotation.txt')
        print(save_path)

        for obj in bpy.data.objects:
            listName.append(obj.name)
            rotation = obj.rotation_euler
            x = int(math.degrees(rotation.x))
            y = int(math.degrees(rotation.y))
            z = int(math.degrees(rotation.z))
            listVal.append((x,y,z))

        for i in range(1, cntObj + 1):
            data += f'{listName[i-1]},{listVal[i-1]},\n'
            
        f = open(save_path, 'w')
        f.write(data)
        f.close()
            
        return {'FINISHED'}
