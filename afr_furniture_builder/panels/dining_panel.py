import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty
from ..utils.library_utils import (
    DINING_LIBRARY_PATH,
    DINING_TABLE_ITEMS,
    DINING_CHAIR_ITEMS,
    find_dining_set_root,
    reposition_chairs,
)
from ..utils import branding


def _gap_updated(self, context):
    active = context.active_object
    root   = find_dining_set_root(active) if active else None
    if root is None:
        stored = self.active_set_name
        if stored and stored in bpy.data.objects:
            root = bpy.data.objects[stored]
    if root and root.get("afr_is_dining_set"):
        reposition_chairs(root, self.live_gap)


class DiningSettings(bpy.types.PropertyGroup):
    library_path: StringProperty(
        name="Library",
        description="Path to AFR Dining Furniture.blend",
        subtype='FILE_PATH',
        default=DINING_LIBRARY_PATH,
    )
    table_name: EnumProperty(
        name="Table",
        items=DINING_TABLE_ITEMS,
        default="Brooklyn_rectangle_dining_table_uv_nov17",
    )
    chair_name: EnumProperty(
        name="Chair",
        items=DINING_CHAIR_ITEMS,
        default="Nexus Chair",
    )
    chair_count: EnumProperty(
        name="Chairs",
        items=[
            ('2', '2-Top', 'Two chairs'),
            ('4', '4-Top', 'Four chairs'),
            ('6', '6-Top', 'Six chairs'),
            ('8', '8-Top', 'Eight chairs'),
        ],
        default='4',
    )
    arrangement: EnumProperty(
        name="Arrangement",
        items=[
            ('RADIAL', 'Radial', 'Chairs evenly spaced around the table radius'),
            ('RECT',   'Rect',   'Chairs aligned to table edges (front/back)'),
        ],
        default='RECT',
    )
    live_gap: FloatProperty(
        name="Gap",
        description="Distance between chair front and table edge",
        default=0.10,
        min=-0.50, max=0.80,
        step=1, precision=3,
        unit='LENGTH',
        update=_gap_updated,
    )
    use_tablecloth: BoolProperty(
        name="Tablecloth",
        description="Add a cloth-simulated tablecloth to the set",
        default=False,
    )
    tablecloth_shape: EnumProperty(
        name="Cloth Shape",
        items=[
            ('RECT',  'Rectangular', 'Rectangular tablecloth'),
            ('ROUND', 'Round',       'Round tablecloth — best for round tables'),
        ],
        default='RECT',
    )
    tablecloth_overhang: FloatProperty(
        name="Overhang",
        description="How far the cloth drapes past each table edge",
        default=0.30,
        min=0.05, max=1.00,
        step=1, precision=3,
        unit='LENGTH',
    )
    active_set_name: StringProperty(name="Active Set", default="")


class DINING_PT_Main(bpy.types.Panel):
    bl_label       = "Dining Sets"
    bl_idname      = "DINING_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "AFR Furniture"
    bl_order       = 4

    def draw_header(self, context):
        ic = branding.icon("icon_dining")
        if ic:
            self.layout.label(text="", icon_value=ic)

    def draw(self, context):
        layout = self.layout
        s = context.scene.dining_settings

        # ── Library ───────────────────────────────────────────
        lib_box = layout.box()
        lib_box.label(text="Library", icon='FILE_FOLDER')
        lib_box.prop(s, "library_path", text="")

        layout.separator(factor=0.8)

        # ── Products ──────────────────────────────────────────
        prod_box = layout.box()
        prod_box.label(text="Products", icon='OBJECT_DATA')
        prod_box.prop(s, "table_name", text="Table")
        prod_box.prop(s, "chair_name", text="Chair")

        layout.separator(factor=0.8)

        # ── Layout ────────────────────────────────────────────
        cfg_box = layout.box()
        cfg_box.label(text="Layout", icon='GRID')
        row = cfg_box.row(align=True)
        row.prop(s, "chair_count", expand=True)
        row = cfg_box.row(align=True)
        row.prop(s, "arrangement", expand=True)

        layout.separator(factor=0.8)

        # ── Tablecloth ────────────────────────────────────────
        cloth_box = layout.box()
        row = cloth_box.row(align=True)
        row.prop(
            s, "use_tablecloth", text="",
            icon='CHECKBOX_HLT' if s.use_tablecloth else 'CHECKBOX_DEHLT',
            emboss=False,
        )
        row.label(text="Tablecloth", icon='MOD_CLOTH')
        if s.use_tablecloth:
            sub = cloth_box.column(align=True)
            sub.row(align=True).prop(s, "tablecloth_shape", expand=True)
            sub.prop(s, "tablecloth_overhang", slider=True)
            sub.separator(factor=0.4)
            sub.label(text="Press Space in Timeline to run sim", icon='INFO')

        layout.separator(factor=0.8)

        # ── Active set & gap ──────────────────────────────────
        active = context.active_object
        root   = find_dining_set_root(active) if active else None
        set_box = layout.box()
        col = set_box.column(align=True)
        col.label(text="Active Set", icon='ARMATURE_DATA')

        if root and root.get("afr_is_dining_set"):
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
        row.operator("dining.build_set", text="Build Dining Set", icon='MESH_PLANE')


classes = [DiningSettings, DINING_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dining_settings = bpy.props.PointerProperty(type=DiningSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.dining_settings
