from .build_set import CAFE_OT_BuildSet

classes = [CAFE_OT_BuildSet]


def register():
    import bpy
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
