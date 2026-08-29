from .match_name import MatchName
from .block_sort import BlockSort
from .export_uv import ExportUV
from .export_obj import ExportOBJ
from .export_fbx import ExportFBX
from .collision_maker import CollisionMaker
from .picking_maker import PickingMaker
from .clean_setting import CleanSetting
from .block_rotation_info import BlockRotationInfo
from .mission_icon_maker import MissionIconMaker

OPERATOR_CLASSES = (
    BlockSort,
    MatchName,
    ExportUV,
    ExportOBJ,
    ExportFBX,
    CollisionMaker,
    PickingMaker,
    CleanSetting,
    BlockRotationInfo,
    MissionIconMaker,
)
