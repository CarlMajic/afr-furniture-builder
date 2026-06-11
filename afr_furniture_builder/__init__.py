bl_info = {
    "name":        "AFR Furniture Builder",
    "author":      "Majic Production Services",
    "version":     (0, 2, 0),
    "blender":     (3, 6, 0),
    "location":    "View3D > Sidebar > AFR Furniture",
    "description": "Place AFR furniture sets from the library catalogue",
    "category":    "Object",
}

import bpy
from . import operators, panels


def register():
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
