import bpy
import bmesh
from mathutils import Vector
from ..utils.library_utils import (
    DINING_COLLECTION_CHAIRS,
    DINING_COLLECTION_TABLES,
    DINING_TABLE_ITEMS,
    DINING_CHAIR_ITEMS,
    append_named_object,
    duplicate_hierarchy,
    get_obj_bounds_xy,
    get_obj_max_z,
    compute_dining_chair_placements,
)

_TABLE_LABELS = {v[0]: v[1] for v in DINING_TABLE_ITEMS}
_CHAIR_LABELS = {v[0]: v[1] for v in DINING_CHAIR_ITEMS}


def _tag_chair(chair_root, placement, table_half_w, table_half_d, chair_inward):
    chair_root["afr_type"]           = placement['type']
    chair_root["afr_angle"]          = placement['angle']
    chair_root["afr_dir_x"]          = placement['dir_x']
    chair_root["afr_dir_y"]          = placement['dir_y']
    chair_root["afr_x_offset"]       = placement['x_offset']
    chair_root["afr_table_half_w"]   = table_half_w
    chair_root["afr_table_half_d"]   = table_half_d
    chair_root["afr_chair_inward"]   = chair_inward
    chair_root["afr_table_center_x"] = placement.get('center_x', 0.0)
    chair_root["afr_table_center_y"] = placement.get('center_y', 0.0)


def _place_chair(chair_root, set_root, placement):
    chair_root.parent = set_root
    chair_root.matrix_parent_inverse = set_root.matrix_world.inverted()
    chair_root.location         = Vector((placement['x'], placement['y'], 0.0))
    chair_root.rotation_euler.z = placement['rot_z']


def _add_tablecloth(context, set_root, table_root, cx, cy, half_w, half_d, settings):
    overhang = settings.tablecloth_overhang
    shape    = settings.tablecloth_shape

    # Cloth half-extents include the overhang drape
    cloth_hw = half_w + overhang
    cloth_hd = half_d + overhang

    # Round cloth is always a perfect circle using the larger dimension
    if shape == 'ROUND':
        cloth_hw = cloth_hd = max(cloth_hw, cloth_hd)

    table_top = get_obj_max_z(table_root)
    cloth_z   = table_top + 0.30   # ~1 ft above table surface — cloth falls onto table

    # Build mesh with bmesh (50 segments = 2500 faces, good drape resolution)
    seg  = 50
    mesh = bpy.data.meshes.new("Tablecloth")
    bm   = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=seg, y_segments=seg, size=1.0)

    # Scale verts to final cloth dimensions
    for v in bm.verts:
        v.co.x *= cloth_hw
        v.co.y *= cloth_hd

    # For round cloth, delete vertices outside the circle
    if shape == 'ROUND':
        r2 = cloth_hw * cloth_hw
        outside = [v for v in bm.verts if v.co.x ** 2 + v.co.y ** 2 > r2]
        bmesh.ops.delete(bm, geom=outside, context='VERTS')

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    cloth_obj = bpy.data.objects.new("Tablecloth", mesh)
    context.scene.collection.objects.link(cloth_obj)

    # Parent to set root so it moves with the set
    cloth_obj.parent = set_root
    cloth_obj.matrix_parent_inverse = set_root.matrix_world.inverted()
    cloth_obj.location = Vector((cx, cy, cloth_z))

    # Cloth modifier — cotton-weight preset
    cloth_mod = cloth_obj.modifiers.new("Cloth", 'CLOTH')
    cs = cloth_mod.settings
    cs.quality               = 10
    cs.mass                  = 0.3
    cs.tension_stiffness     = 15.0
    cs.compression_stiffness = 15.0
    cs.shear_stiffness       = 5.0
    cs.bending_stiffness     = 0.5

    col = cloth_mod.collision_settings
    col.use_collision  = True
    col.distance_min   = 0.005

    # Collision modifier on every table mesh so the cloth lands on it
    for obj in [table_root] + list(table_root.children_recursive):
        if obj.type == 'MESH':
            if not any(m.type == 'COLLISION' for m in obj.modifiers):
                obj.modifiers.new("Collision", 'COLLISION')

    return cloth_obj


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
        table_half_w   = (max_x - min_x) / 2
        table_half_d   = (max_y - min_y) / 2
        table_center_x = (min_x + max_x) / 2
        table_center_y = (min_y + max_y) / 2

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
        for p in placements:
            p['x']        += table_center_x
            p['y']        += table_center_y
            p['x_offset'] += table_center_x
            p['center_x']  = table_center_x
            p['center_y']  = table_center_y

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

        # Update matrices so get_obj_max_z reads correct world positions
        context.view_layer.update()

        if s.use_tablecloth:
            _add_tablecloth(
                context, set_root, table_root,
                table_center_x, table_center_y,
                table_half_w, table_half_d,
                s,
            )

        context.view_layer.update()

        s.active_set_name = set_root.name

        bpy.ops.object.select_all(action='DESELECT')
        set_root.select_set(True)
        context.view_layer.objects.active = set_root

        self.report({'INFO'}, f"Built: {set_name}")
        return {'FINISHED'}
