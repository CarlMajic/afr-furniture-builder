import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty
from ..utils.library_utils import (
    LOUNGE_LIBRARY_PATH,
    COCKTAIL_TABLE_ITEMS,
    SOFA_ITEMS,
    LOUNGE_CHAIR_ITEMS,
    END_TABLE_ITEMS,
    ACCENT_ITEMS,
    LAMP_ITEMS,
    find_lounge_set_root,
    reposition_lounge_set,
)
from ..utils import branding


def _update_sofa_gap(self, context):
    root = _active_lounge_root(self, context)
    if root:
        reposition_lounge_set(root, self.sofa_gap, self.chair_gap, self.chair_spread)


def _update_chair_gap(self, context):
    root = _active_lounge_root(self, context)
    if root:
        reposition_lounge_set(root, self.sofa_gap, self.chair_gap, self.chair_spread)


def _update_chair_spread(self, context):
    root = _active_lounge_root(self, context)
    if root:
        reposition_lounge_set(root, self.sofa_gap, self.chair_gap, self.chair_spread)


def _active_lounge_root(self, context):
    active = context.active_object
    root   = find_lounge_set_root(active) if active else None
    if root is None:
        stored = self.active_set_name
        if stored and stored in bpy.data.objects:
            root = bpy.data.objects[stored]
    if root and root.get("afr_is_lounge_set"):
        return root
    return None


class LoungeSettings(bpy.types.PropertyGroup):
    library_path: StringProperty(
        name="Library",
        description="Path to AFR Lounge Furniture.blend",
        subtype='FILE_PATH',
        default=LOUNGE_LIBRARY_PATH,
    )
    cocktail_table_name: EnumProperty(
        name="Coffee Table",
        items=COCKTAIL_TABLE_ITEMS,
        default="Civic Cocktail Table",
    )
    sofa_name: EnumProperty(
        name="Sofa",
        items=SOFA_ITEMS,
        default="Blanc Sofa",
    )
    chair_name: EnumProperty(
        name="Chair",
        items=LOUNGE_CHAIR_ITEMS,
        default="Blanc Chair",
    )
    use_end_table: BoolProperty(name="End Table", default=False)
    end_table_name: EnumProperty(
        name="End Table",
        items=END_TABLE_ITEMS,
        default="Civic End Table",
    )
    use_accent: BoolProperty(name="Accent", default=False)
    accent_name: EnumProperty(
        name="Accent",
        items=ACCENT_ITEMS,
        default="Corbin_Divider",
    )
    use_lamp: BoolProperty(name="Lamp", default=False)
    lamp_name: EnumProperty(
        name="Lamp",
        items=LAMP_ITEMS,
        default="alura_lamp",
    )
    sofa_gap: FloatProperty(
        name="Sofa Gap",
        description="Y shift from library position (0 = as designed)",
        default=0.0,
        min=-1.50, max=1.50,
        step=1, precision=3,
        unit='LENGTH',
        update=_update_sofa_gap,
    )
    chair_gap: FloatProperty(
        name="Chair Gap",
        description="Y shift from library position (0 = as designed)",
        default=0.0,
        min=-1.50, max=1.50,
        step=1, precision=3,
        unit='LENGTH',
        update=_update_chair_gap,
    )
    chair_spread: FloatProperty(
        name="Chair Spread",
        description="Additional X offset per chair from library position (0 = as designed)",
        default=0.0,
        min=-2.0, max=2.0,
        step=1, precision=3,
        unit='LENGTH',
        update=_update_chair_spread,
    )
    active_set_name: StringProperty(name="Active Set", default="")


class LOUNGE_PT_Main(bpy.types.Panel):
    bl_label       = "Lounge Sets"
    bl_idname      = "LOUNGE_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "AFR Furniture"

    def draw_header(self, context):
        logo = branding.icon()
        if logo:
            self.layout.label(text="", icon_value=logo)

    def draw(self, context):
        layout = self.layout
        s = context.scene.lounge_settings

        # ── Library ───────────────────────────────────────────
        lib_box = layout.box()
        lib_box.label(text="Library", icon='FILE_FOLDER')
        lib_box.prop(s, "library_path", text="")

        layout.separator(factor=0.8)

        # ── Products ──────────────────────────────────────────
        prod_box = layout.box()
        prod_box.label(text="Products", icon='OBJECT_DATA')
        prod_box.prop(s, "cocktail_table_name", text="Coffee Table")
        prod_box.prop(s, "sofa_name",           text="Sofa")
        prod_box.prop(s, "chair_name",          text="Chair")

        layout.separator(factor=0.8)

        # ── Optional pieces ───────────────────────────────────
        opt_box = layout.box()
        opt_box.label(text="Optional Pieces", icon='ADD')

        row = opt_box.row(align=True)
        row.prop(s, "use_end_table", text="", icon='CHECKBOX_HLT' if s.use_end_table else 'CHECKBOX_DEHLT', emboss=False)
        row.label(text="End Table")
        sub = row.row()
        sub.enabled = s.use_end_table
        sub.prop(s, "end_table_name", text="")

        row = opt_box.row(align=True)
        row.prop(s, "use_accent", text="", icon='CHECKBOX_HLT' if s.use_accent else 'CHECKBOX_DEHLT', emboss=False)
        row.label(text="Accent")
        sub = row.row()
        sub.enabled = s.use_accent
        sub.prop(s, "accent_name", text="")

        row = opt_box.row(align=True)
        row.prop(s, "use_lamp", text="", icon='CHECKBOX_HLT' if s.use_lamp else 'CHECKBOX_DEHLT', emboss=False)
        row.label(text="Lamp")
        sub = row.row()
        sub.enabled = s.use_lamp
        sub.prop(s, "lamp_name", text="")

        layout.separator(factor=0.8)

        # ── Active set & spacing ──────────────────────────────
        active = context.active_object
        root   = find_lounge_set_root(active) if active else None
        set_box = layout.box()
        col = set_box.column(align=True)
        col.label(text="Active Set", icon='ARMATURE_DATA')

        if root and root.get("afr_is_lounge_set"):
            col.label(text=root.name, icon='CHECKMARK')
        else:
            stored = s.active_set_name
            if stored and stored in bpy.data.objects:
                col.label(text=stored, icon='OBJECT_DATA')
            else:
                col.label(text="No set selected", icon='INFO')

        col.separator(factor=0.5)
        col.prop(s, "sofa_gap",     slider=True)
        col.prop(s, "chair_gap",    slider=True)
        col.prop(s, "chair_spread", slider=True)

        layout.separator(factor=1.2)

        # ── Build ─────────────────────────────────────────────
        row = layout.row()
        row.scale_y = 1.6
        row.operator("lounge.build_set", text="Build Lounge Set", icon='MESH_PLANE')


classes = [LoungeSettings, LOUNGE_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lounge_settings = bpy.props.PointerProperty(type=LoungeSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lounge_settings
