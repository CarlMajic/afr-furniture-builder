import bpy
import sys
from bpy.props import StringProperty, EnumProperty, FloatProperty
from ..utils.library_utils import (
    LIBRARY_PATH,
    TABLE_ITEMS,
    CHAIR_ITEMS,
    find_cafe_set_root,
    reposition_chairs,
)


def _gap_updated(self, context):
    """Called live on every drag of the gap slider."""
    active = context.active_object
    root = find_cafe_set_root(active) if active else None

    # Fall back to the last-built set if nothing suitable is selected
    if root is None:
        stored = self.active_set_name
        if stored and stored in bpy.data.objects:
            root = bpy.data.objects[stored]

    if root and root.get("afr_is_cafe_set"):
        reposition_chairs(root, self.live_gap)


class CafeSettings(bpy.types.PropertyGroup):
    library_path: StringProperty(
        name="Library",
        description="Path to AFR Cafe Seating Furniture.blend",
        subtype='FILE_PATH',
        default=LIBRARY_PATH,
    )
    table_name: EnumProperty(
        name="Table",
        items=TABLE_ITEMS,
        default="arlo_cafe_table_black",
    )
    chair_name: EnumProperty(
        name="Chair",
        items=CHAIR_ITEMS,
        default="Sonic Chair",
    )
    chair_count: EnumProperty(
        name="Chairs",
        items=[
            ('2', '2-Top', 'Two chairs'),
            ('4', '4-Top', 'Four chairs'),
        ],
        default='4',
    )
    arrangement: EnumProperty(
        name="Arrangement",
        items=[
            ('RADIAL', 'Radial', 'Chairs evenly spaced around the table radius'),
            ('RECT',   'Rect',   'Chairs aligned to table edges (front/back/sides)'),
        ],
        default='RADIAL',
    )
    live_gap: FloatProperty(
        name="Gap",
        description="Space between chair front and table edge (drag to adjust selected set live)",
        default=0.10,
        min=-0.50,
        max=0.80,
        step=1,
        precision=3,
        unit='LENGTH',
        update=_gap_updated,
    )
    active_set_name: StringProperty(
        name="Active Set",
        default="",
    )


class CAFE_OT_Reload(bpy.types.Operator):
    bl_idname      = "cafe.reload_addon"
    bl_label       = "Reload Addon"
    bl_description = "Hot-reload AFR Furniture Builder without restarting Blender"

    def execute(self, context):
        mods = [k for k in sys.modules if k == "afr_furniture_builder" or k.startswith("afr_furniture_builder.")]
        for mod in mods:
            del sys.modules[mod]
        bpy.ops.preferences.addon_disable(module="afr_furniture_builder")
        bpy.ops.preferences.addon_enable(module="afr_furniture_builder")
        return {'FINISHED'}


class CAFE_PT_Main(bpy.types.Panel):
    bl_label       = "Cafe Sets"
    bl_idname      = "CAFE_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "AFR Furniture"

    def draw(self, context):
        layout = self.layout
        s = context.scene.cafe_settings

        # --- Library path ---
        box = layout.box()
        box.prop(s, "library_path", text="")

        layout.separator()

        # --- Furniture pickers ---
        layout.prop(s, "table_name",  text="Table")
        layout.prop(s, "chair_name",  text="Chair")

        layout.separator()

        # --- Set configuration ---
        row = layout.row(align=True)
        row.prop(s, "chair_count",  expand=True)
        layout.prop(s, "arrangement", expand=True)

        layout.separator()

        # --- Gap slider ---
        active = context.active_object
        root = find_cafe_set_root(active) if active else None

        gap_box = layout.box()
        col = gap_box.column()

        if root and root.get("afr_is_cafe_set"):
            col.label(text=f"Set: {root.name}", icon='OBJECT_DATA')
        else:
            stored = s.active_set_name
            if stored and stored in bpy.data.objects:
                col.label(text=f"Last: {stored}", icon='OBJECT_DATA')
            else:
                col.label(text="No set selected", icon='INFO')

        col.prop(s, "live_gap", slider=True)

        layout.separator()

        # --- Build button ---
        layout.operator("cafe.build_set", text="Build Set", icon='MESH_PLANE')

        layout.separator()
        layout.operator("cafe.reload_addon", text="Reload Addon", icon='FILE_REFRESH')


classes = [CafeSettings, CAFE_OT_Reload, CAFE_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.cafe_settings = bpy.props.PointerProperty(type=CafeSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.cafe_settings
