import bpy
from mathutils import Vector
from ..utils.library_utils import (
    DINING_COLLECTION_CHAIRS,
    DINING_COLLECTION_TABLES,
    DINING_TABLE_ITEMS,
    DINING_CHAIR_ITEMS,
    append_named_object,
    duplicate_hierarchy,
    get_obj_bounds_xy,
    compute_dining_chair_placements,
)

_TABLE_LABELS = {v[0]: v[1] for v in DINING_TABLE_ITEMS}
_CHAIR_LABELS = {v[0]: v[1] for v in DINING_CHAIR_ITEMS}


def _tag_chair(chair_root, placement, table_half_w, table_half_d, chair_inward):
    chair_root["afr_type"]          = placement['type']
    chair_root["afr_angle"]         = placement['angle']
    chair_root["afr_dir_x"]         = placement['dir_x']
    chair_root["afr_dir_y"]         = placement['dir_y']
    chair_root["afr_x_offset"]      = placement['x_offset']
    chair_root["afr_table_half_w"]  = table_half_w
    chair_root["afr_table_half_d"]  = table_half_d
    chair_root["afr_chair_inward"]  = chair_inward


def _place_chair(chair_root, set_root, placement):
    chair_root.parent = set_root
    chair_root.matrix_parent_inverse = set_root.matrix_world.inverted()
    chair_root.location         = Vector((placement['x'], placement['y'], 0.0))
    chair_root.rotation_euler.z = placement['rot_z']


class DINING_OT_BuildSet(bpy.types.Operator):
    bl_idname      = "dining.build_set"
    bl_label       = "Build Dining Set"
    bl_description = "Place a dining table with chairs from the AFR library"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s     = context.scene.dining_settings
        lib   = s.library_path
        count = int(s.chair_count)
        gap_m = s.live_gap

        try:
            table_root = append_named_object(lib, DINING_COLLECTION_TABLES, s.table_name)
        except Exception as exc:
            self.report({'ERROR'}, f"Table: {exc}")
            return {'CANCELLED'}

        min_x, max_x, min_y, max_y = get_obj_bounds_xy(table_root)
        table_half_w = (max_x - min_x) / 2
        table_half_d = (max_y - min_y) / 2

        try:
            first_chair = append_named_object(lib, DINING_COLLECTION_CHAIRS, s.chair_name)
        except Exception as exc:
            bpy.data.objects.remove(table_root, do_unlink=True)
            self.report({'ERROR'}, f"Chair: {exc}")
            return {'CANCELLED'}

        _, _, c_min_y, _ = get_obj_bounds_xy(first_chair)
        chair_inward = c_min_y

        placements = compute_dining_chair_placements(
            table_half_w, table_half_d, chair_inward, gap_m, count, s.arrangement
        )

        set_name = (
            f"{_TABLE_LABELS.get(s.table_name, s.table_name)}"
            f" | {_CHAIR_LABELS.get(s.chair_name, s.chair_name)}"
            f" {count}-Top"
        )
        set_root = bpy.data.objects.new(set_name, None)
        set_root.empty_display_size = 0.05
        set_root["afr_is_dining_set"] = True
        set_root["afr_gap"]           = gap_m
        context.scene.collection.objects.link(set_root)

        table_root.parent = set_root
        table_root.matrix_parent_inverse = set_root.matrix_world.inverted()
        table_root.location = Vector((0, 0, 0))

        _tag_chair(first_chair, placements[0], table_half_w, table_half_d, chair_inward)
        _place_chair(first_chair, set_root, placements[0])

        for i in range(1, count):
            chair_copy = duplicate_hierarchy(first_chair)
            _tag_chair(chair_copy, placements[i], table_half_w, table_half_d, chair_inward)
            _place_chair(chair_copy, set_root, placements[i])

        context.view_layer.update()

        s.active_set_name = set_root.name

        bpy.ops.object.select_all(action='DESELECT')
        set_root.select_set(True)
        context.view_layer.objects.active = set_root

        self.report({'INFO'}, f"Built: {set_name}")
        return {'FINISHED'}
