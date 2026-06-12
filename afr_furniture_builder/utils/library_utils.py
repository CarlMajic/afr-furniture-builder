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

    # Find the target root: no parent, name matches.
    # Exact match first — handles names like "Escape Chair.001" where the
    # numeric suffix is part of the actual library name, not a Blender dedup
    # artifact.  Fall back to base-name match for dedup copies.
    target_root = None
    for name in sorted(new_names):
        obj = bpy.data.objects[name]
        if obj.parent is not None:
            continue
        if name == object_name:
            target_root = obj
            break

    if target_root is None:
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

    # Snapshot the full hierarchy and each object's children BEFORE copying.
    # obj.copy() inherits the parent of the original, so children lists grow
    # during copying and cause KeyErrors in the reparent pass.
    all_originals = [source_root] + list(source_root.children_recursive)
    children_map  = {obj: list(obj.children) for obj in all_originals}

    old_to_new = {}
    for obj in all_originals:
        new_obj = obj.copy()
        if obj.data is not None:
            new_obj.data = obj.data   # linked duplicate — share mesh data
        new_obj.parent = None         # detach the inherited parent immediately
        scene_col.objects.link(new_obj)
        old_to_new[obj] = new_obj

    for obj in all_originals:
        new_obj = old_to_new[obj]
        for child in children_map[obj]:
            if child not in old_to_new:
                continue
            new_child = old_to_new[child]
            new_child.parent = new_obj
            new_child.matrix_parent_inverse = child.matrix_parent_inverse.copy()
            new_child.location       = child.location.copy()
            new_child.rotation_euler = child.rotation_euler.copy()
            new_child.scale          = child.scale.copy()

    return old_to_new[source_root]


# ---------------------------------------------------------------------------
# Chair placement math
#
# After the inward-rotation fix (rot_z = angle - π/2), local +Y points AWAY
# from the table.  The chair face nearest the table is therefore local min_y
# (the inward face), NOT max_y.
#
# Placement formula:  r = table_half + gap - chair_inward
#   chair_inward = mesh_min_y of chair at origin (the inward-facing edge).
#   At gap=0 the inward face is flush with the table edge.
#   Negative gap tucks the chair under the table.
# ---------------------------------------------------------------------------

def compute_chair_placements(table_half_w, table_half_d, chair_inward, gap_m, count, arrangement):
    """
    Returns list of placement dicts: x, y, rot_z, type, angle, dir_x, dir_y, x_offset.
    chair_inward: bounding-box min-Y of chair at origin (inward face after rotation).

    RECT 4-top: 2 chairs side-by-side on the front, 2 mirrored on the back.
    X offset = table_half_w / 2 so each pair is evenly spread across the table edge.
    """
    placements = []

    if arrangement == 'RADIAL':
        table_radius = max(table_half_w, table_half_d)
        r = table_radius + gap_m - chair_inward
        start = -math.pi / 2
        angles = [start + i * 2 * math.pi / count for i in range(count)]
        for angle in angles:
            placements.append({
                'x':        r * math.cos(angle),
                'y':        r * math.sin(angle),
                'rot_z':    angle - math.pi / 2,
                'type':     'radial',
                'angle':    angle,
                'dir_x':    math.cos(angle),
                'dir_y':    math.sin(angle),
                'x_offset': 0.0,
            })

    else:  # RECT
        front_y  = table_half_d + gap_m - chair_inward
        chair_x  = table_half_w / 2   # X spread for 2-per-side pairs

        if count == 2:
            # One chair centred on each long side
            raw = [
                (0,        -front_y,  math.pi,  0,   -1),  # front centre
                (0,        +front_y,  0.0,       0,   +1),  # back centre
            ]
            for x, y, rot_z, dx, dy in raw:
                placements.append({
                    'x': x, 'y': y, 'rot_z': rot_z,
                    'type': 'rect', 'angle': 0.0,
                    'dir_x': float(dx), 'dir_y': float(dy),
                    'x_offset': 0.0,
                })
        else:
            # Two chairs per side — front pair then back pair
            pairs = [
                (-chair_x, -front_y, math.pi, -1),  # front left
                (+chair_x, -front_y, math.pi, +1),  # front right
                (-chair_x, +front_y, 0.0,      -1),  # back left
                (+chair_x, +front_y, 0.0,      +1),  # back right
            ]
            for x, y, rot_z, x_sign in pairs:
                placements.append({
                    'x': x, 'y': y, 'rot_z': rot_z,
                    'type': 'rect', 'angle': 0.0,
                    'dir_x': 0.0, 'dir_y': -1.0 if y < 0 else 1.0,
                    'x_offset': float(x_sign) * chair_x,
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


def find_bar_set_root(obj):
    """Traverse parent chain to find the AFR high-seating set root empty."""
    current = obj
    while current is not None:
        if current.get("afr_is_bar_set"):
            return current
        current = current.parent
    return None


# ---------------------------------------------------------------------------
# High Seating library constants
# ---------------------------------------------------------------------------

BAR_LIBRARY_PATH = r"D:\Blender\Decore\AFR Furniture\AFR High Seating Furniture.blend"

BAR_TABLE_ITEMS = [
    ("arlo_bar_table_black",                          "Arlo Black",           ""),
    ("Aspen_bar_table",                               "Aspen",                ""),
    ("Baja_Bar_table",                                "Baja",                 ""),
    ("Bar Table Black Base Black Top 36''",           "36\" Black/Black",     ""),
    ("Bar Table Black Base White Top 30''",           "30\" Black/White",     ""),
    ("Bar Table Chrome Base Maple Top 30''",          "30\" Chrome/Maple",    ""),
    ("Chardonnay Bar Table",                          "Chardonnay",           ""),
    ("Cylinder Buffet Table 6'",                      "Cylinder Buffet 6ft",  ""),
    ("Cylinder Pub Table 30 inch",                    "Cylinder Pub 30\"",    ""),
    ("Cylinder Pub Table 42 inch",                    "Cylinder Pub 42\"",    ""),
    ("Java Pub Table",                                "Java Pub",             ""),
    ("koolGLOBarTable-Rectangle",                     "Kool GLO Rectangle",   ""),
    ("Melina Bar Table v1",                           "Melina",               ""),
    ("Memphis Rectangle Pub Table",                   "Memphis Rectangle",    ""),
    ("Memphis Square Pub table",                      "Memphis Square",       ""),
    ("24in_square_cosmo_bar_top_black_frame",         "24\" Cosmo Black",     ""),
    ("24in_square_cosmo_bar_top_chrome_frame",        "24\" Cosmo Chrome",    ""),
    ("24in_square_cosmo_bar_top_tulip_frame",         "24\" Cosmo Tulip",     ""),
    ("24in_square_emerald_bar_top_black_frame",       "24\" Emerald Black",   ""),
    ("24in_square_emerald_bar_top_chrome_frame",      "24\" Emerald Chrome",  ""),
    ("32in_round_yukon_gold_bar_table_with_black_base", "32\" Yukon Gold",    ""),
    ("6ft Rectangular Bar Table",                     "6ft Rectangular",      ""),
]

BAR_STOOL_ITEMS = [
    ("arlo_stool_black",              "Arlo Black",          ""),
    ("Baja_Bar_Stool",               "Baja",                 ""),
    ("Caprice Stool",                "Caprice",              ""),
    ("clarabarstool",                "Clara",                ""),
    ("colin_bar_stool",              "Colin",                ""),
    ("Criss Cross Stool  Espresso",  "Criss Cross Espresso", ""),
    ("Eclipse Stool",                "Eclipse",              ""),
    ("Equino Stool Black'",          "Equino Black",         ""),
    ("Escape Chair.001",             "Escape",               ""),
    ("Euro Bar",                     "Euro Bar",             ""),
    ("ghost_stoo",                   "Ghost",                ""),
    ("Hourglass Bar Stool Black",    "Hourglass Black",      ""),
    ("Hourglass Bar Stool White",    "Hourglass White",      ""),
    ("milo_stool_black",             "Milo Black",           ""),
    ("nexusBarstool",                "Nexus",                ""),
    ("Regal bar stool",              "Regal",                ""),
    ("Silk Back Bar Stool- Blue",    "Silk Back Blue",       ""),
    ("vienna stool grey_ low poly",  "Vienna Grey",          ""),
    ("zuri_chair v2",                "Zuri",                 ""),
]


# ---------------------------------------------------------------------------
# Lounge library constants
# ---------------------------------------------------------------------------

LOUNGE_LIBRARY_PATH = r"D:\Blender\Decore\AFR Furniture\AFR Lounge Furniture.blend"

COLLECTION_COCKTAIL       = "Cocktail Tables"
COLLECTION_SOFAS          = "Sofas"
COLLECTION_LOUNGE_CHAIRS  = "Chairs Stools"
COLLECTION_END_TABLES     = "End Tables"
COLLECTION_ACCENTS        = "Accents"
COLLECTION_LAMPS          = "Lamps"

COCKTAIL_TABLE_ITEMS = [
    ("baja_table",                              "Baja",                  ""),
    ("Civic Cocktail Table",                    "Civic",                 ""),
    ("Costa Cocktail Table",                    "Costa",                 ""),
    ("cubecocktailtable",                       "Cube",                  ""),
    ("Evoke Cocktail Table",                    "Evoke",                 ""),
    ("Fuse cocktail table",                     "Fuse",                  ""),
    ("gemma_accent_table_blue_agate",           "Gemma Blue Agate",      ""),
    ("Greystone Cocktail Table",                "Greystone",             ""),
    ("hemingway_cocktail_table",                "Hemingway",             ""),
    ("kool_glo_cocktail_table",                 "Kool GLO",              ""),
    ("London_Cocktail_Table_uv_lowpoly_nov18",  "London",                ""),
    ("Novel End ",                              "Novel",                 ""),
    ("Pentagram",                               "Pentagram",             ""),
    ("Pia Cocktail Table",                      "Pia",                   ""),
    ("Quasar Cocttail Table",                   "Quasar",                ""),
    ("tribeca cocktail table",                  "Tribeca",               ""),
    ("tulum_cocktail_table",                    "Tulum",                 ""),
    ("Vivid Cocktail Table",                    "Vivid",                 ""),
]

SOFA_ITEMS = [
    ("andes_sofa",                          "Andes",                        ""),
    ("annabella_sofa",                      "Annabella",                    ""),
    ("Aurora Sofa",                         "Aurora",                       ""),
    ("baja_sofa",                           "Baja",                         ""),
    ("Blanc Loveseat",                      "Blanc Loveseat",               ""),
    ("Blanc Sofa",                          "Blanc Sofa",                   ""),
    ("Catalina_left_low poly",              "Catalina Left",                ""),
    ("Chandler Loveseat",                   "Chandler Loveseat",            ""),
    ("Chandler Sofa",                       "Chandler Sofa",                ""),
    ("Chateau Sofa",                        "Chateau",                      ""),
    ("Continental Curved Loveseat",         "Continental Curved",           ""),
    ("Continental Reverse Curved Loveseat", "Continental Reverse Curved",   ""),
    ("costa_sofa",                          "Costa",                        ""),
    ("Cromwell Sofa",                       "Cromwell",                     ""),
    ("evoke_sofa",                          "Evoke",                        ""),
    ("Grammercy Armless Loveseat",          "Grammercy Armless Loveseat",   ""),
    ("Grammercy Armless Sofa",              "Grammercy Armless Sofa",       ""),
    ("Jade_sofa_low poly",                  "Jade",                         ""),
    ("jasper_sofa",                         "Jasper",                       ""),
    ("lyla_sofa",                           "Lyla",                         ""),
    ("Madison_sofa_low poly",               "Madison",                      ""),
    ("Mango Sofa",                          "Mango",                        ""),
    ("mangosofa",                           "Mango (alt)",                  ""),
    ("Metro Loveseat",                      "Metro Loveseat",               ""),
    ("Metro Sofa",                          "Metro Sofa",                   ""),
    ("monacosofa",                          "Monaco",                       ""),
    ("Montana_Mocha_Sofa_uv_nov18",         "Montana Mocha Sofa",           ""),
    ("Montana_mocha_loveseat_uv_nov18",     "Montana Mocha Loveseat",       ""),
    ("Niko Loveseat",                       "Niko Loveseat",                ""),
    ("Niko Sofa",                           "Niko Sofa",                    ""),
    ("Oliver_sofa low poly",                "Oliver",                       ""),
    ("Parma Loveseat",                      "Parma Loveseat",               ""),
    ("Parma Sofa",                          "Parma Sofa",                   ""),
    ("Penelope Sofa",                       "Penelope",                     ""),
    ("Regale Chaise",                       "Regale Chaise",                ""),
    ("Regale Sofa",                         "Regale Sofa",                  ""),
    ("Sophistication Armless Loveseat",     "Sophistication Armless LS",    ""),
    ("Sophistication Armless Sofa",         "Sophistication Armless Sofa",  ""),
    ("Suave Midnight",                      "Suave Midnight (single)",      ""),
    ("Suave Midnight Loveseat",             "Suave Midnight Loveseat",      ""),
    ("Suave Midnight Sofa",                 "Suave Midnight Sofa",          ""),
    ("tulum_loveseat",                      "Tulum Loveseat",               ""),
    ("tulum_sofa",                          "Tulum Sofa",                   ""),
    ("verona_sofa",                         "Verona",                       ""),
    ("Whisper Loveseat",                    "Whisper Loveseat",             ""),
    ("Whisper Sofa",                        "Whisper Sofa",                 ""),
    ("Winston Sofa",                        "Winston",                      ""),
    ("Zeppelin Sctional",                   "Zeppelin Sectional",           ""),
]

LOUNGE_CHAIR_ITEMS = [
    ("andes_chair",                          "Andes",                       ""),
    ("annabella_chair",                      "Annabella",                   ""),
    ("aubrey_chair",                         "Aubrey",                      ""),
    ("Aurora Chair",                         "Aurora",                      ""),
    ("baja_chair",                           "Baja",                        ""),
    ("Bianca_Chair",                         "Bianca",                      ""),
    ("Blanc Chair",                          "Blanc",                       ""),
    ("Boca Armless Chair Charged_low poly",  "Boca Armless",                ""),
    ("bocacornerchaircharged_low poly",      "Boca Corner",                 ""),
    ("Buckskin Stage Chair",                 "Buckskin Stage",              ""),
    ("Chandler Chair",                       "Chandler",                    ""),
    ("Chateau Elan Chair",                   "Chateau Elan",                ""),
    ("costa chiar",                          "Costa",                       ""),
    ("costa_chair",                          "Costa (alt)",                 ""),
    ("Cromwell_Chair",                       "Cromwell",                    ""),
    ("Empire Chair",                         "Empire",                      ""),
    ("Evoke Chair",                          "Evoke",                       ""),
    ("Function Armless Chair",               "Function Armless",            ""),
    ("Function Corner",                      "Function Corner",             ""),
    ("Grammercy Armless Chair",              "Grammercy Armless",           ""),
    ("Grammercy Corner",                     "Grammercy Corner",            ""),
    ("group1",                               "Group 1",                     ""),
    ("hemingway_armless_chair",              "Hemingway Armless",           ""),
    ("hemingway_corner",                     "Hemingway Corner",            ""),
    ("jasper_chair",                         "Jasper",                      ""),
    ("Jade_chair_low poly",                  "Jade",                        ""),
    ("lyla_chair",                           "Lyla",                        ""),
    ("Madison_chair_low poly",               "Madison",                     ""),
    ("mangochair",                           "Mango",                       ""),
    ("Metro Chair",                          "Metro",                       ""),
    ("monacochair_low poly",                 "Monaco",                      ""),
    ("monarchchair",                         "Monarch",                     ""),
    ("Montana_mocha_chair_uv_nov18",         "Montana Mocha",               ""),
    ("Niko Chair",                           "Niko",                        ""),
    ("Oliver_chair_low poly",                "Oliver",                      ""),
    ("Parma_chair",                          "Parma",                       ""),
    ("Patrice Tablet Chair",                 "Patrice Tablet",              ""),
    ("Penelope Chair",                       "Penelope",                    ""),
    ("Sophistication Armless Chair",         "Sophistication Armless",      ""),
    ("Sophistication Corner",                "Sophistication Corner",       ""),
    ("Suave Midnight Chair",                 "Suave Midnight",              ""),
    ("tulum_chair",                          "Tulum",                       ""),
    ("tulum_nest_chair",                     "Tulum Nest",                  ""),
    ("verona_chair",                         "Verona",                      ""),
    ("Whisper Chair",                        "Whisper",                     ""),
    ("Winston Chair",                        "Winston",                     ""),
]

END_TABLE_ITEMS = [
    ("Ava End Table",                  "Ava",                    ""),
    ("Azaria_Accent_Table",            "Azaria",                 ""),
    ("Civic End Table",                "Civic",                  ""),
    ("Cylinder End Table",             "Cylinder",               ""),
    ("Eden Accent Table - Large",      "Eden Large",             ""),
    ("Evoke Cube",                     "Evoke Cube",             ""),
    ("Evoke End Table",                "Evoke",                  ""),
    ("Fuse  Sofa table_low poly",      "Fuse Sofa Table",        ""),
    ("Fuse Pedestal",                  "Fuse Pedestal",          ""),
    ("Fuze_End_T",                     "Fuze",                   ""),
    ("Greystone End Table",            "Greystone",              ""),
    ("Hylton Tablet Table",            "Hylton Tablet",          ""),
    ("Java Accent Table",              "Java",                   ""),
    ("koolGLOBarTable-24inSq",         "Kool GLO Bar 24\"",      ""),
    ("koolGLOCafeTable-24inSq",        "Kool GLO Cafe 24\"",     ""),
    ("kool_glo_end_table",             "Kool GLO End",           ""),
    ("Light_cube",                     "Light Cube",             ""),
    ("London_End_Table_uv_nov18",      "London End",             ""),
    ("London_Pedestal_uv_nov18",       "London Pedestal",        ""),
    ("Mon Table",                      "Mon",                    ""),
    ("Oro mirrored cube",              "Oro Mirrored Cube",      ""),
    ("Oyster Accent Table",            "Oyster",                 ""),
    ("Pentagram End Table",            "Pentagram",              ""),
    ("Phoebe Table Gold",              "Phoebe Gold",            ""),
    ("Pia End Table",                  "Pia",                    ""),
    ("Porto Accent Table",             "Porto",                  ""),
    ("Rose Table",                     "Rose",                   ""),
    ("sirona_accent_table",            "Sirona",                 ""),
    ("tulum_end_table",                "Tulum",                  ""),
    ("Vivid End0",                     "Vivid",                  ""),
    ("Woodland Accent Table - Large",  "Woodland Large",         ""),
    ("Woodland Accent Table - Medium", "Woodland Medium",        ""),
    ("Woodland Accent Table - Small",  "Woodland Small",         ""),
    ("ZANZIBAR T",                     "Zanzibar",               ""),
]

ACCENT_ITEMS = [
    ("Blaze Dividerrface14",          "Blaze Divider",          ""),
    ("Corbin_Divider",                "Corbin Divider",         ""),
    ("Greystone Console Table",       "Greystone Console",      ""),
    ("London_sofa_table_uv_nov18",    "London Sofa Table",      ""),
    ("vivid sofa table",              "Vivid Sofa Table",       ""),
    ("vortexdivider",                 "Vortex Divider",         ""),
]

LAMP_ITEMS = [
    ("alura_lamp",       "Alura",   ""),
    ("circuit_floorlamp","Circuit", ""),
    ("motif_floorlamp",  "Motif",   ""),
]


def find_dining_set_root(obj):
    """Traverse parent chain to find the AFR dining set root empty."""
    current = obj
    while current is not None:
        if current.get("afr_is_dining_set"):
            return current
        current = current.parent
    return None


def _rect_x_positions(per_side, table_half_w):
    """Evenly spaced X positions for per_side chairs across the table width."""
    if per_side == 1:
        return [0.0]
    outer = table_half_w * 0.75
    return [-outer + outer * 2.0 * i / (per_side - 1) for i in range(per_side)]


def compute_dining_chair_placements(table_half_w, table_half_d, chair_inward, gap_m, count, arrangement):
    """Like compute_chair_placements but supports 2/4/6/8 chairs for dining."""
    placements = []

    if arrangement == 'RADIAL':
        table_radius = max(table_half_w, table_half_d)
        r = table_radius + gap_m - chair_inward
        start = -math.pi / 2
        angles = [start + i * 2 * math.pi / count for i in range(count)]
        for angle in angles:
            placements.append({
                'x':        r * math.cos(angle),
                'y':        r * math.sin(angle),
                'rot_z':    angle - math.pi / 2,
                'type':     'radial',
                'angle':    angle,
                'dir_x':    math.cos(angle),
                'dir_y':    math.sin(angle),
                'x_offset': 0.0,
            })
    else:  # RECT
        front_y     = table_half_d + gap_m - chair_inward
        per_side    = count // 2
        x_positions = _rect_x_positions(per_side, table_half_w)

        for x in x_positions:
            placements.append({
                'x': x, 'y': -front_y, 'rot_z': math.pi,
                'type': 'rect', 'angle': 0.0,
                'dir_x': 0.0, 'dir_y': -1.0,
                'x_offset': x,
            })
        for x in x_positions:
            placements.append({
                'x': x, 'y': +front_y, 'rot_z': 0.0,
                'type': 'rect', 'angle': 0.0,
                'dir_x': 0.0, 'dir_y': +1.0,
                'x_offset': x,
            })

    return placements


def find_lounge_set_root(obj):
    """Traverse parent chain to find the AFR lounge set root empty."""
    current = obj
    while current is not None:
        if current.get("afr_is_lounge_set"):
            return current
        current = current.parent
    return None


def reposition_lounge_set(set_root, sofa_gap, chair_gap, chair_spread):
    """Reposition all lounge set pieces when sliders change."""
    set_root["afr_sofa_gap"]     = sofa_gap
    set_root["afr_chair_gap"]    = chair_gap
    set_root["afr_chair_spread"] = chair_spread

    for child in set_root.children:
        role = child.get("afr_lounge_role")
        if role == "sofa":
            child.location.y = sofa_gap
        elif role == "chair_r":
            child.location.y = -chair_gap
            child.location.x =  chair_spread
        elif role == "chair_l":
            child.location.y = -chair_gap
            child.location.x = -chair_spread
        elif role in ("end_table", "accent", "lamp"):
            nat_y = child.get("afr_natural_y", 0.0)
            child.location.y = nat_y + sofa_gap


def reposition_chairs(set_root, gap_m):
    """Move all chairs in a placed set to reflect a new gap value."""
    set_root["afr_gap"] = gap_m
    for child in set_root.children:
        ptype = child.get("afr_type")
        if not ptype:
            continue

        chair_inward = child.get("afr_chair_inward", 0.0)
        half_w = child.get("afr_table_half_w", 0.4)
        half_d = child.get("afr_table_half_d", 0.4)

        if ptype == 'radial':
            angle = child.get("afr_angle", 0.0)
            r = max(half_w, half_d) + gap_m - chair_inward
            child.location.x = r * math.cos(angle)
            child.location.y = r * math.sin(angle)

        elif ptype == 'rect':
            dir_y    = child.get("afr_dir_y", -1.0)
            x_offset = child.get("afr_x_offset", 0.0)
            center_y = child.get("afr_table_center_y", 0.0)
            r = half_d + gap_m - chair_inward
            child.location.x = x_offset
            child.location.y = dir_y * r + center_y


# ---------------------------------------------------------------------------
# Dining library constants
# ---------------------------------------------------------------------------

DINING_LIBRARY_PATH      = r"D:\Blender\Decore\AFR Furniture\AFR Dining Furniture.blend"
DINING_COLLECTION_TABLES = "Tables"
DINING_COLLECTION_CHAIRS = "Chairs Stools"

DINING_TABLE_ITEMS = [
    ("Aspen Dining Table_low poly",              "Aspen",               ""),
    ("Brio Dining Table",                        "Brio",                ""),
    ("Brooklyn_rectangle_dining_table_uv_nov17", "Brooklyn Rectangle",  ""),
    ("brooklyn_round_dining_table_uv_nov17",     "Brooklyn Round",      ""),
    ("cora_dining_table",                        "Cora",                ""),
    ("Cylinder Dining Table",                    "Cylinder",            ""),
    ("Elements table",                           "Elements",            ""),
    ("encore_dining_table",                      "Encore",              ""),
    ("Java Dining Table",                        "Java",                ""),
    ("kool GLO café table - 60in",          "Kool GLO 60\"",       ""),
    ("madera_dining_table",                      "Madera",              ""),
    ("Tahoe_dining_table_uv_nov18",              "Tahoe",               ""),
    ("Vivid_Rectangle_Table_Glass",              "Vivid Rectangle Glass",""),
    ("Vivid_Square_Table_Glass",                 "Vivid Square Glass",  ""),
]

DINING_CHAIR_ITEMS = [
    ("arlo_chair_black",                "Arlo Black",              ""),
    ("Bianca_Chair",                    "Bianca",                  ""),
    ("Caprice Chair",                   "Caprice",                 ""),
    ("ClaraChair",                      "Clara",                   ""),
    ("colin_chair",                     "Colin",                   ""),
    ("Criss Cros",                      "Criss Cross",             ""),
    ("Elio Chair",                      "Elio",                    ""),
    ("Escape Chair",                    "Escape",                  ""),
    ("ghost_chai",                      "Ghost",                   ""),
    ("leslie chair",                    "Leslie",                  ""),
    ("milo_chair_black",                "Milo Black",              ""),
    ("Nexus Chair",                     "Nexus",                   ""),
    ("Regale Chair",                    "Regale",                  ""),
    ("Silk Back Armless Chair - Black", "Silk Back Armless Black", ""),
    ("Sonic Chair",                     "Sonic",                   ""),
    ("zazu_cafe_chair",                 "Zazu",                    ""),
]
