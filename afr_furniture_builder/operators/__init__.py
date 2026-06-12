from .build_set import CAFE_OT_BuildSet
from .build_bar_set import BAR_OT_BuildSet
from .build_lounge_set import LOUNGE_OT_BuildSet
from .build_dining_set import DINING_OT_BuildSet

classes = [CAFE_OT_BuildSet, BAR_OT_BuildSet, LOUNGE_OT_BuildSet, DINING_OT_BuildSet]


def register():
    import bpy
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
