"""Run this script in Blender's Text Editor to hot-reload the addon during development."""
import bpy
import sys

addon = "afr_furniture_builder"

mods = [k for k in sys.modules if k == addon or k.startswith(addon + ".")]
for m in mods:
    del sys.modules[m]

bpy.ops.preferences.addon_disable(module=addon)
bpy.ops.preferences.addon_enable(module=addon)
print(f"Reloaded: {addon}")
