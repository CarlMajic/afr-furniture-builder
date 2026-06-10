bl_info = {
    "name":        "AFR Cafe Builder",
    "author":      "Majic Production Services",
    "version":     (0, 1, 0),
    "blender":     (3, 6, 0),
    "location":    "View3D > Sidebar > AFR Cafe",
    "description": "Place AFR cafe table + chair sets from the furniture library",
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
