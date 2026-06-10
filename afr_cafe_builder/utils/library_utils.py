import bpy
import os
import math
from mathutils import Vector

LIBRARY_PATH = r"D:\Blender\Decore\AFR Furniture\AFR Cafe Seating Furniture.blend"
COLLECTION_CHAIRS = "Chairs Stools"
COLLECTION_TABLES = "Tables"

TABLE_ITEMS = [
    ("arlo_cafe_table_black",                         "Arlo Black (30\")",           "Arlo 30\" round cafe table, black"),
    ("Cafe Table Black Base Black Top 30''",           "30\" Black/Black",            "30\" round, black base, black top"),
    ("Cafe Table Black Base Black Top 36''",           "36\" Black/Black",            "36\" round, black base, black top"),
    ("24in_square_cosmo_cafe_top_chrome_frame",        "24\" Square Cosmo Chrome",    "24\" square, chrome frame"),
    ("24in_square_emerald_cafe_table_black_frame",     "24\" Square Emerald Black",   "24\" square, black frame"),
    ("32in_round_cement_cafe_table_with_black_base",   "32\" Round Cement Black",     "32\" round cement top, black base"),
    ("32in_round_cement_cafe_table_with_chrome_base",  "32\" Round Cement Chrome",    "32\" round cement top, chrome base"),
    ("6footrectangularwhitecafetable",                 "6ft Rectangular White",       "6ft rectangular white cafe table"),
    ("koolGLOBarTable-36inSq",                        "Kool GLO 36\" Bar",           "36\" square Kool GLO light-up bar table"),
    ("koolGLOCafeTable-Rectangle",                    "Kool GLO Rectangle",          "Rectangular Kool GLO light-up cafe table"),
]

CHAIR_ITEMS = [
    ("arlo_chair_black",                  "Arlo Black",              ""),
    ("Bianca_Chair",                      "Bianca",                  ""),
    ("Caprice Chair",                     "Caprice",                 ""),
    ("ClaraChair",                        "Clara",                   ""),
    ("colin_chair",                       "Colin",                   ""),
    ("Criss Cros",                        "Criss Cross",             ""),
    ("Cromwell_Chair",                    "Cromwell",                ""),
    ("Elio Chair",                        "Elio",                    ""),
    ("Empire Chair",                      "Empire",                  ""),
    ("Escape Chair",                      "Escape",                  ""),
    ("ghost_chai",                        "Ghost",                   ""),
    ("leslie chair",                      "Leslie",                  ""),
    ("milo_chair_black",                  "Milo Black",              ""),
    ("Nexus Chair",                       "Nexus",                   ""),
    ("Regale Chair",                      "Regale",                  ""),
    ("Silk Back Armless Chair - Black",   "Silk Back Armless Black", ""),
    ("Sonic Chair",                       "Sonic",                   ""),
    ("zazu_cafe_chair",                   "Zazu",                    ""),
]


# ---------------------------------------------------------------------------
# Bounding box helpers
# ---------------------------------------------------------------------------

def get_obj_bounds_xy(obj):
    """World-space XY extents of an object and its mesh children."""
    meshes = [obj] if obj.type == 'MESH' else []
    for child in obj.children_recursive:
        if child.type == 'MESH':
            meshes.append(child)

    if not meshes:
        return 0.0, 0.0, 0.0, 0.0

    corners = []
    for m in meshes:
        for c in m.bound_box:
            corners.append(m.matrix_world @ Vector(c))

    return (
        min(v.x for v in corners),
        max(v.x for v in corners),
        min(v.y for v in corners),
        max(v.y for v in corners),
    )


# ---------------------------------------------------------------------------
# Library append
# ---------------------------------------------------------------------------

def _is_dedup_suffix(s):
    return s.isdigit()


def append_named_object(library_path, collection_name, object_name):
    """
    Append a single named root object + its full hierarchy from a library collection.
    Calls view_layer.update() before returning so matrix_world is valid.
    Returns the root object linked to the scene collection.
    """
    if not os.path.exists(library_path):
        raise FileNotFoundError(f"Library not found: {library_path}")

    before = set(bpy.data.objects.keys())

    with bpy.data.libraries.load(library_path, link=False) as (src, dst):
        if collection_name not in src.collections:
            raise RuntimeError(f"Collection '{collection_name}' not in library")
        dst.collections = [collection_name]

    new_names = set(bpy.data.objects.keys()) - before

    # Find the target root: no parent, name matches (strip .001 dedup suffix)
    target_root = None
    for name in sorted(new_names):
        obj = bpy.data.objects[name]
        if obj.parent is not None:
            continue
        parts = name.rsplit('.', 1)
        base = parts[0] if len(parts) == 2 and _is_dedup_suffix(parts[1]) else name
        if base == object_name:
            target_root = obj
            break

    if target_root is None:
        for name in new_names:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        raise RuntimeError(f"'{object_name}' not found in '{collection_name}'")

    keep = {target_root} | set(target_root.children_recursive)

    for name in sorted(new_names):
        obj = bpy.data.objects.get(name)
        if obj and obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)

    scene_col = bpy.context.scene.collection
    for obj in keep:
        if not any(c == scene_col for c in obj.users_collection):
            try:
                scene_col.objects.link(obj)
            except RuntimeError:
                pass

    # Update matrices so bounding box queries are correct
    bpy.context.view_layer.update()

    return target_root


# ---------------------------------------------------------------------------
# Hierarchy duplicate (shares mesh data)
# ---------------------------------------------------------------------------

def duplicate_hierarchy(source_root):
    """
    Linked duplicate of source_root + all children.
    Returns new root (in scene collection, unparented).
    """
    scene_col = bpy.context.scene.collection
    old_to_new = {}

    def _copy(obj):
        new_obj = obj.copy()
        new_obj.data = obj.data
        scene_col.objects.link(new_obj)
        old_to_new[obj] = new_obj
        for child in obj.children:
            _copy(child)

    _copy(source_root)

    def _reparent(obj):
        new_obj = old_to_new[obj]
        for child in obj.children:
            new_child = old_to_new[child]
            new_child.parent = new_obj
            new_child.matrix_parent_inverse = child.matrix_parent_inverse.copy()
            new_child.location       = child.location.copy()
            new_child.rotation_euler = child.rotation_euler.copy()
            new_child.scale          = child.scale.copy()
            _reparent(child)

    _reparent(source_root)
    return old_to_new[source_root]


# ---------------------------------------------------------------------------
# Chair placement math
#
# Chairs in this library face +Y by default (sitter looks toward +Y).
# chair_front = mesh_max_y when chair is at origin = seat-front offset from origin.
#
# Placement formula:  r = table_half_in_direction + gap + chair_front
#   This positions the chair so its seat front is exactly `gap` past the table edge.
#
# Rotation formula (inward-facing): rot_z = angle + π/2
#   Rotates chair so its local +Y points toward the table center.
# ---------------------------------------------------------------------------

def compute_chair_placements(table_half_w, table_half_d, chair_front, gap_m, count, arrangement):
    """
    Returns list of placement dicts: x, y, rot_z, type, angle, dir_x, dir_y.
    chair_front: bounding-box max-Y of chair at origin (seat front offset).
    """
    placements = []

    if arrangement == 'RADIAL':
        table_radius = max(table_half_w, table_half_d)
        r = table_radius + gap_m + chair_front
        # First chair at front (-Y side), then evenly spaced clockwise
        start = -math.pi / 2
        angles = [start + i * 2 * math.pi / count for i in range(count)]
        for angle in angles:
            placements.append({
                'x':     r * math.cos(angle),
                'y':     r * math.sin(angle),
                'rot_z': angle + math.pi / 2,   # +Y faces toward origin
                'type':  'radial',
                'angle': angle,
                'dir_x': math.cos(angle),
                'dir_y': math.sin(angle),
            })

    else:  # RECT
        front_y = table_half_d + gap_m + chair_front
        side_x  = table_half_w + gap_m + chair_front

        if count == 2:
            raw = [
                (0,       -front_y,  0.0,            0,  -1),  # front: faces +Y
                (0,       +front_y,  math.pi,         0,  +1),  # back:  faces -Y
            ]
        else:
            raw = [
                (0,       -front_y,  0.0,             0,  -1),  # front
                (0,       +front_y,  math.pi,          0,  +1),  # back
                (-side_x,  0,       -math.pi / 2,     -1,   0),  # left:  faces +X
                (+side_x,  0,        math.pi / 2,     +1,   0),  # right: faces -X
            ]

        for x, y, rot_z, dx, dy in raw:
            placements.append({
                'x': x, 'y': y, 'rot_z': rot_z,
                'type': 'rect',
                'angle': 0.0,
                'dir_x': float(dx),
                'dir_y': float(dy),
            })

    return placements


# ---------------------------------------------------------------------------
# Live gap repositioning
# ---------------------------------------------------------------------------

def find_cafe_set_root(obj):
    """Traverse parent chain to find the AFR cafe set root empty."""
    current = obj
    while current is not None:
        if current.get("afr_is_cafe_set"):
            return current
        current = current.parent
    return None


def reposition_chairs(set_root, gap_m):
    """Move all chairs in a placed set to reflect a new gap value."""
    set_root["afr_gap"] = gap_m
    for child in set_root.children:
        ptype = child.get("afr_type")
        if not ptype:
            continue

        chair_front = child.get("afr_chair_front", 0.5)
        half_w = child.get("afr_table_half_w", 0.4)
        half_d = child.get("afr_table_half_d", 0.4)

        if ptype == 'radial':
            angle = child.get("afr_angle", 0.0)
            r = max(half_w, half_d) + gap_m + chair_front
            child.location.x = r * math.cos(angle)
            child.location.y = r * math.sin(angle)

        elif ptype == 'rect':
            dir_x = child.get("afr_dir_x", 0.0)
            dir_y = child.get("afr_dir_y", -1.0)
            if abs(dir_y) >= abs(dir_x):
                r = half_d + gap_m + chair_front
                child.location.x = 0.0
                child.location.y = dir_y * r
            else:
                r = half_w + gap_m + chair_front
                child.location.x = dir_x * r
                child.location.y = 0.0
