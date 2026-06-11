import bpy
from mathutils import Vector
from ..utils.library_utils import (
    COLLECTION_CHAIRS,
    COLLECTION_TABLES,
    BAR_TABLE_ITEMS,
    BAR_STOOL_ITEMS,
    append_named_object,
    duplicate_hierarchy,
    get_obj_bounds_xy,
    compute_chair_placements,
)

_TABLE_LABELS = {v[0]: v[1] for v in BAR_TABLE_ITEMS}
_STOOL_LABELS = {v[0]: v[1] for v in BAR_STOOL_ITEMS}


def _tag_stool(stool_root, placement, table_half_w, table_half_d, stool_inward):
    stool_root["afr_type"]         = placement['type']
    stool_root["afr_angle"]        = placement['angle']
    stool_root["afr_dir_x"]        = placement['dir_x']
    stool_root["afr_dir_y"]        = placement['dir_y']
    stool_root["afr_x_offset"]     = placement['x_offset']
    stool_root["afr_table_half_w"] = table_half_w
    stool_root["afr_table_half_d"] = table_half_d
    stool_root["afr_chair_inward"] = stool_inward


def _place_stool(stool_root, set_root, placement):
    stool_root.parent = set_root
    stool_root.matrix_parent_inverse = set_root.matrix_world.inverted()
    stool_root.location         = Vector((placement['x'], placement['y'], 0.0))
    stool_root.rotation_euler.z = placement['rot_z']


class BAR_OT_BuildSet(bpy.types.Operator):
    bl_idname      = "bar.build_set"
    bl_label       = "Build Bar Set"
    bl_description = "Place a high-seating table with stools from the AFR library"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s     = context.scene.bar_settings
        lib   = s.library_path
        count = int(s.stool_count)
        gap_m = s.live_gap

        try:
            table_root = append_named_object(lib, COLLECTION_TABLES, s.table_name)
        except Exception as exc:
            self.report({'ERROR'}, f"Table: {exc}")
            return {'CANCELLED'}

        min_x, max_x, min_y, max_y = get_obj_bounds_xy(table_root)
        table_half_w = (max_x - min_x) / 2
        table_half_d = (max_y - min_y) / 2

        try:
            first_stool = append_named_object(lib, COLLECTION_CHAIRS, s.stool_name)
        except Exception as exc:
            bpy.data.objects.remove(table_root, do_unlink=True)
            self.report({'ERROR'}, f"Stool: {exc}")
            return {'CANCELLED'}

        _, _, s_min_y, _ = get_obj_bounds_xy(first_stool)
        stool_inward = s_min_y

        placements = compute_chair_placements(
            table_half_w, table_half_d, stool_inward, gap_m, count, s.arrangement
        )

        set_name = (
            f"{_TABLE_LABELS.get(s.table_name, s.table_name)}"
            f" | {_STOOL_LABELS.get(s.stool_name, s.stool_name)}"
            f" {count}-Top"
        )
        set_root = bpy.data.objects.new(set_name, None)
        set_root.empty_display_size = 0.05
        set_root["afr_is_bar_set"] = True
        set_root["afr_gap"]        = gap_m
        context.scene.collection.objects.link(set_root)

        table_root.parent = set_root
        table_root.matrix_parent_inverse = set_root.matrix_world.inverted()
        table_root.location = Vector((0, 0, 0))

        _tag_stool(first_stool, placements[0], table_half_w, table_half_d, stool_inward)
        _place_stool(first_stool, set_root, placements[0])

        for i in range(1, count):
            stool_copy = duplicate_hierarchy(first_stool)
            _tag_stool(stool_copy, placements[i], table_half_w, table_half_d, stool_inward)
            _place_stool(stool_copy, set_root, placements[i])

        context.view_layer.update()

        s.active_set_name = set_root.name

        bpy.ops.object.select_all(action='DESELECT')
        set_root.select_set(True)
        context.view_layer.objects.active = set_root

        self.report({'INFO'}, f"Built: {set_name}")
        return {'FINISHED'}
