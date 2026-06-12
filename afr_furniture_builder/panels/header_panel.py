import bpy
from ..utils import branding


class AFR_PT_Header(bpy.types.Panel):
    bl_label       = "AFR Furniture Builder"
    bl_idname      = "AFR_PT_header"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "AFR Furniture"
    bl_order       = 0
    bl_options     = {'HIDE_HEADER'}

    def draw(self, context):
        branding.draw_logo(self.layout, scale=5.0)


classes = [AFR_PT_Header]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
