import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty
from ..utils.library_utils import (
    BAR_LIBRARY_PATH,
    BAR_TABLE_ITEMS,
    BAR_STOOL_ITEMS,
    find_bar_set_root,
    reposition_chairs,
)
from ..utils import branding


def _gap_updated(self, context):
    active = context.active_object
    root   = find_bar_set_root(active) if active else None
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
            ('RECT',   'Rect',   'Stools aligned to table edges (front/back)'),
        ],
        default='RADIAL',
    )
    live_gap: FloatProperty(
        name="Gap",
        description="Distance between stool front and table edge",
        default=0.10,
        min=-0.50, max=0.80,
        step=1, precision=3,
        unit='LENGTH',
        update=_gap_updated,
    )
    active_set_name: StringProperty(name="Active Set", default="")


class BAR_PT_Main(bpy.types.Panel):
    bl_label       = "High Seating"
    bl_idname      = "BAR_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "AFR Furniture"
    bl_order       = 2

    def draw_header(self, context):
        ic = branding.icon("icon_bar")
        if ic:
            self.layout.label(text="", icon_value=ic)

    def draw(self, context):
        layout = self.layout
        s = context.scene.bar_settings

        # ── Library ───────────────────────────────────────────
        lib_box = layout.box()
        lib_box.label(text="Library", icon='FILE_FOLDER')
        lib_box.prop(s, "library_path", text="")

        layout.separator(factor=0.8)

        # ── Products ──────────────────────────────────────────
        prod_box = layout.box()
        prod_box.label(text="Products", icon='OBJECT_DATA')
        prod_box.prop(s, "table_name", text="Table")
        prod_box.prop(s, "stool_name", text="Stool")

        layout.separator(factor=0.8)

        # ── Layout ────────────────────────────────────────────
        cfg_box = layout.box()
        cfg_box.label(text="Layout", icon='GRID')
        row = cfg_box.row(align=True)
        row.prop(s, "stool_count", expand=True)
        row = cfg_box.row(align=True)
        row.prop(s, "arrangement", expand=True)

        layout.separator(factor=0.8)

        # ── Active set & gap ──────────────────────────────────
        active = context.active_object
        root   = find_bar_set_root(active) if active else None
        set_box = layout.box()
        col = set_box.column(align=True)
        col.label(text="Active Set", icon='ARMATURE_DATA')

        if root and root.get("afr_is_bar_set"):
            col.label(text=root.name, icon='CHECKMARK')
        else:
            stored = s.active_set_name
            if stored and stored in bpy.data.objects:
                col.label(text=stored, icon='OBJECT_DATA')
            else:
                col.label(text="No set selected", icon='INFO')

        col.separator(factor=0.5)
        col.prop(s, "live_gap", slider=True)

        layout.separator(factor=1.2)

        # ── Build ─────────────────────────────────────────────
        row = layout.row()
        row.scale_y = 1.6
        row.operator("bar.build_set", text="Build High Seating Set", icon='MESH_PLANE')


classes = [BarSettings, BAR_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bar_settings = bpy.props.PointerProperty(type=BarSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bar_settings
