import math
import os

import bpy


class MissionIconMaker(bpy.types.Operator):
    """미션 아이콘을 생성합니다."""
    bl_idname = "object.mission_icon_maker"
    bl_label = "Mission Icon Maker"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 사용할 렌더링 엔진 설정 및 카메라 렌더링 배경 투명도 True
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.resolution_x = 256
        bpy.context.scene.render.resolution_y = 256

        # Save Directiry
        file_path = bpy.data.filepath
        export_dir = os.path.dirname(file_path) + "/MissionIcon/"

        # Check directory
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            print("Create folder")
        else:
            print("Exist folder:", export_dir)

        # Camera 변수
        cam_name = "RenderCamera"
        cam_location = (0, -8.2668, 0)
        cam_rotation = (90, 0, 0)

        # 씬에 카메라 추가(location & rotation setting)
        def add_camera_to_scene(name, location, rotation):
            bpy.ops.object.camera_add(location=location)
            camera = bpy.context.object
            camera.name = name
            bpy.context.scene.camera = camera
            camera.rotation_euler = [math.radians(rotation[0]), math.radians(rotation[1]), math.radians(rotation[2])]
            camera.data.type = 'ORTHO'
            camera.data.ortho_scale = 1.0


        # 카메라와 생성
        add_camera_to_scene(cam_name, cam_location, cam_rotation)

        # 3D 뷰포트 영역 활성화
        area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        area.spaces[0].region_3d.view_perspective = 'CAMERA'

        # 오버레이 숨기기
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.overlay.show_overlays = False


        # -------------- mission icon make ----------------


        objList = []

        # except 'Camera' in objList
        for obj in bpy.data.objects:
            if (obj.name == cam_name):
                print("Camera or Light")
            else :
                objList.append(obj)
                obj.location = (10, 0, 0)
                
        # 미션 아이콘 이미지 렌더링
        for obj in objList:
            obj.hide_set(False, view_layer=None)
            obj.location = (0, 0, 0)
            bpy.context.scene.render.filepath = export_dir + obj.name + '_Icon.png'
            bpy.context.scene.render.image_settings.file_format = 'PNG'
            bpy.ops.render.opengl(write_still=True)
            obj.location = (10, 0, 0)
            

        # 블럭 재정렬
        xPos, yPos, zPos = 0.5, 0.5, 0.5
        column = 10

        #objs = bpy.context.selected_objects
        objList.sort(key = lambda o: o.name)

        for obj in objList:
            obj.location = (xPos, yPos, zPos)
            if xPos < (column - 1):
                xPos += 1.0
            elif xPos > (column - 1):
                xPos = 0.5
                yPos -= 1.0
                zPos -= 1.0

        # 카메라 제거
        for cam in bpy.data.cameras:
            bpy.data.cameras.remove(cam)
            
        return {'FINISHED'}
