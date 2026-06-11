import bpy
import sys
from bpy.props import StringProperty, EnumProperty, FloatProperty
from ..utils.library_utils import (
    BAR_LIBRARY_PATH,
    BAR_TABLE_ITEMS,
    BAR_STOOL_ITEMS,
    find_bar_set_root,
    reposition_chairs,
)


def _gap_updated(self, context):
    active = context.active_object
    root = find_bar_set_root(active) if active else None

    if root is None:
        stored = self.active_set_name
        if stored and stored in bpy.data.objects:
            root = bpy.data.objects[stored]

    if root and root.get("afr_is_bar_set"):
        reposition_chairs(root, self.live_gap)


class BarSettings(bpy.types.PropertyGroup):
    library_path: StringProperty(
        name="Library",
        description="Path to AFR High Seating Furniture.blend",
        subtype='FILE_PATH',
        default=BAR_LIBRARY_PATH,
    )
    table_name: EnumProperty(
        name="Table",
        items=BAR_TABLE_ITEMS,
        default="arlo_bar_table_black",
    )
    stool_name: EnumProperty(
        name="Stool",
        items=BAR_STOOL_ITEMS,
        default="arlo_stool_black",
    )
    stool_count: EnumProperty(
        name="Stools",
        items=[
            ('2', '2-Top', 'Two stools'),
            ('4', '4-Top', 'Four stools'),
        ],
        default='4',
    )
    arrangement: EnumProperty(
        name="Arrangement",
        items=[
            ('RADIAL', 'Radial', 'Stools evenly spaced around the table radius'),
            ('RECT',   'Rect',   'Stools aligned to table edges (front/back/sides)'),
        ],
        default='RADIAL',
    )
    live_gap: FloatProperty(
        name="Gap",
        description="Space between stool front and table edge (drag to adjust selected set live)",
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


class BAR_PT_Main(bpy.types.Panel):
    bl_label       = "High Seating Sets"
    bl_idname      = "BAR_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "AFR Furniture"

    def draw(self, context):
        layout = self.layout
        s = context.scene.bar_settings

        box = layout.box()
        box.prop(s, "library_path", text="")

        layout.separator()

        layout.prop(s, "table_name", text="Table")
        layout.prop(s, "stool_name", text="Stool")

        layout.separator()

        row = layout.row(align=True)
        row.prop(s, "stool_count", expand=True)
        layout.prop(s, "arrangement", expand=True)

        layout.separator()

        active = context.active_object
        root = find_bar_set_root(active) if active else None

        gap_box = layout.box()
        col = gap_box.column()

        if root and root.get("afr_is_bar_set"):
            col.label(text=f"Set: {root.name}", icon='OBJECT_DATA')
        else:
            stored = s.active_set_name
            if stored and stored in bpy.data.objects:
                col.label(text=f"Last: {stored}", icon='OBJECT_DATA')
            else:
                col.label(text="No set selected", icon='INFO')

        col.prop(s, "live_gap", slider=True)

        layout.separator()

        layout.operator("bar.build_set", text="Build Set", icon='MESH_PLANE')


classes = [BarSettings, BAR_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bar_settings = bpy.props.PointerProperty(type=BarSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bar_settings
