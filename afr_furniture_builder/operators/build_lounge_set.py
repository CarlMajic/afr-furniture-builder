import bpy
from mathutils import Vector
from ..utils.library_utils import (
    COLLECTION_COCKTAIL,
    COLLECTION_SOFAS,
    COLLECTION_LOUNGE_CHAIRS,
    COLLECTION_END_TABLES,
    COLLECTION_ACCENTS,
    COLLECTION_LAMPS,
    COCKTAIL_TABLE_ITEMS,
    SOFA_ITEMS,
    LOUNGE_CHAIR_ITEMS,
    append_named_object,
    duplicate_hierarchy,
    get_obj_bounds_xy,
)

_COCKTAIL_LABELS = {v[0]: v[1] for v in COCKTAIL_TABLE_ITEMS}
_SOFA_LABELS     = {v[0]: v[1] for v in SOFA_ITEMS}
_CHAIR_LABELS    = {v[0]: v[1] for v in LOUNGE_CHAIR_ITEMS}


def _tag(obj, role, natural_y=0.0):
    """Store the role and natural-position Y offset for reposition."""
    obj["afr_lounge_role"] = role
    obj["afr_natural_y"]   = natural_y


def _parent(child, root, x=0.0, y=0.0):
    """Parent child to root at (x, y) with no rotation change."""
    child.parent = root
    child.matrix_parent_inverse = root.matrix_world.inverted()
    child.location         = Vector((x, y, 0.0))
    child.rotation_euler.z = 0.0


class LOUNGE_OT_BuildSet(bpy.types.Operator):
    bl_idname      = "lounge.build_set"
    bl_label       = "Build Lounge Set"
    bl_description = "Place an AFR lounge set from the library"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s            = context.scene.lounge_settings
        lib          = s.library_path
        sofa_gap     = s.sofa_gap
        chair_gap    = s.chair_gap
        chair_spread = s.chair_spread
        pieces = []

        def _append(collection, name, label):
            try:
                obj = append_named_object(lib, collection, name)
                pieces.append(obj)
                return obj
            except Exception as exc:
                self.report({'ERROR'}, f"{label}: {exc}")
                return None

        def _abort():
            for p in pieces:
                try:
                    bpy.data.objects.remove(p, do_unlink=True)
                except Exception:
                    pass
            return {'CANCELLED'}

        # ── Coffee table ──────────────────────────────────────────────────
        coffee = _append(COLLECTION_COCKTAIL, s.cocktail_table_name, "Coffee table")
        if coffee is None:
            return _abort()

        # ── Sofa ──────────────────────────────────────────────────────────
        sofa = _append(COLLECTION_SOFAS, s.sofa_name, "Sofa")
        if sofa is None:
            return _abort()
        # Need sofa back-face Y to anchor lamp/accent behind it
        _, _, s_min_y, s_max_y = get_obj_bounds_xy(sofa)

        # ── Lounge chairs ─────────────────────────────────────────────────
        chair = _append(COLLECTION_LOUNGE_CHAIRS, s.chair_name, "Chair")
        if chair is None:
            return _abort()

        # Duplicate for the mirrored second chair
        chair2 = duplicate_hierarchy(chair)
        pieces.append(chair2)

        # ── Optional end table ────────────────────────────────────────────
        end_table = None
        if s.use_end_table:
            end_table = _append(COLLECTION_END_TABLES, s.end_table_name, "End table")
            if end_table is None:
                return _abort()

        # ── Optional accent ───────────────────────────────────────────────
        accent = None
        accent_natural_y = 0.0
        if s.use_accent:
            accent = _append(COLLECTION_ACCENTS, s.accent_name, "Accent")
            if accent is None:
                return _abort()
            _, _, ac_min_y, _ = get_obj_bounds_xy(accent)
            accent_natural_y = s_max_y - ac_min_y

        # ── Optional lamp ─────────────────────────────────────────────────
        lamp = None
        lamp_natural_y = 0.0
        if s.use_lamp:
            lamp = _append(COLLECTION_LAMPS, s.lamp_name, "Lamp")
            if lamp is None:
                return _abort()
            _, _, lp_min_y, _ = get_obj_bounds_xy(lamp)
            lamp_natural_y = s_max_y - lp_min_y

        # ── Build set root ────────────────────────────────────────────────
        set_name = (
            f"{_SOFA_LABELS.get(s.sofa_name, s.sofa_name)}"
            f" | {_COCKTAIL_LABELS.get(s.cocktail_table_name, s.cocktail_table_name)}"
            f" | {_CHAIR_LABELS.get(s.chair_name, s.chair_name)}"
        )
        set_root = bpy.data.objects.new(set_name, None)
        set_root.empty_display_size = 0.1
        set_root["afr_is_lounge_set"] = True
        set_root["afr_sofa_gap"]      = sofa_gap
        set_root["afr_chair_gap"]     = chair_gap
        set_root["afr_chair_spread"]  = chair_spread
        context.scene.collection.objects.link(set_root)

        # Coffee table — at set origin, library orientation unchanged
        _tag(coffee, "coffee_table")
        _parent(coffee, set_root)

        # Sofa — library geometry puts it at +Y; gap slider is a delta
        _tag(sofa, "sofa")
        _parent(sofa, set_root, y=sofa_gap)

        # Right chair — library geometry puts it at -Y; spread shifts X
        _tag(chair, "chair_r")
        _parent(chair, set_root, x=chair_spread, y=-chair_gap)

        # Left chair — mirror of right via scale.x = -1
        _tag(chair2, "chair_l")
        _parent(chair2, set_root, x=-chair_spread, y=-chair_gap)
        chair2.scale.x = -1.0

        # Optional end table — library geometry positions it; tracks sofa delta
        if end_table:
            _tag(end_table, "end_table", natural_y=0.0)
            _parent(end_table, set_root, y=sofa_gap)

        # Optional accent — front face at sofa back, tracks sofa delta
        if accent:
            _tag(accent, "accent", natural_y=accent_natural_y)
            _parent(accent, set_root, y=accent_natural_y + sofa_gap)

        # Optional lamp — front face at sofa back, tracks sofa delta
        if lamp:
            _tag(lamp, "lamp", natural_y=lamp_natural_y)
            _parent(lamp, set_root, y=lamp_natural_y + sofa_gap)

        context.view_layer.update()

        s.active_set_name = set_root.name
        bpy.ops.object.select_all(action='DESELECT')
        set_root.select_set(True)
        context.view_layer.objects.active = set_root

        self.report({'INFO'}, f"Built: {set_name}")
        return {'FINISHED'}
