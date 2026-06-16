# AFR Furniture Builder

A Blender add-on for placing AFR furniture sets from library `.blend` files into event layouts. Built for Majic Production Services to mirror the Unreal Engine event-production workflow.

**Version:** 0.4.0  
**Blender:** 5.0+  
**Panel location:** View3D → Sidebar → AFR Furniture tab

---

## Overview

The add-on reads furniture assets from AFR library `.blend` files and places fully-parented sets in the scene. Each set is built around a root empty so the whole group moves together. Live sliders let you fine-tune spacing after placement without rebuilding.

Four builders are included:

| Panel | Library file | What it places |
|-------|-------------|----------------|
| **Cafe Sets** | `AFR Cafe Seating Furniture.blend` | Cafe table + chairs (2 or 4) |
| **High Seating** | `AFR High Seating Furniture.blend` | Bar/pub table + bar stools (2 or 4) |
| **Lounge Sets** | `AFR Lounge Furniture.blend` | Sofa + coffee table + 2 lounge chairs + optional end table, accent, and lamp |
| **Dining Sets** | `AFR Dining Furniture.blend` | Dining table + chairs (2, 4, 6, or 8) + optional tablecloth sim |

The tab also shows the AFR logo at the top and a small category icon next to each panel header.

---

## Installation

1. Zip the `afr_furniture_builder/` folder (the folder itself, not its contents).
2. In Blender: **Edit → Preferences → Add-ons → Install** → select the zip.
3. Enable **AFR Furniture Builder** in the add-on list.

The panel appears in the **N-panel** (View3D sidebar) under the **AFR Furniture** tab.

### Library file paths

Each panel has a **Library** path field at the top. The defaults point to:

```
D:\Blender\Decore\AFR Furniture\AFR Cafe Seating Furniture.blend
D:\Blender\Decore\AFR Furniture\AFR High Seating Furniture.blend
D:\Blender\Decore\AFR Furniture\AFR Lounge Furniture.blend
D:\Blender\Decore\AFR Furniture\AFR Dining Furniture.blend
```

Update these paths in the panel if your library files live elsewhere.

---

## Panel reference

### Cafe Sets

| Control | Effect |
|---------|--------|
| Library | Path to cafe library `.blend` |
| Table | Table model |
| Chair | Chair model |
| Chairs | 2 or 4 chairs |
| Arrangement | Radial (around table radius) or Rect (front/back edges) |
| Gap | Distance between table edge and chair front |
| **Build Cafe Set** | Places the set |

### High Seating

Same controls as Cafe Sets, draws from the bar/pub library.

### Lounge Sets

| Control | Effect |
|---------|--------|
| Library | Path to lounge library `.blend` |
| Coffee Table | Cocktail table model |
| Sofa | Sofa / loveseat model |
| Chair | Lounge chair model |
| End Table *(optional)* | Toggle + model picker |
| Accent *(optional)* | Toggle + model picker |
| Lamp *(optional)* | Toggle + model picker |
| Sofa Gap | Y shift from library position (0 = as designed) |
| Chair Gap | Y shift from library position (0 = as designed) |
| Chair Spread | X offset per chair from library position (0 = as designed) |
| **Build Lounge Set** | Places the set |

Sliders update any active/selected lounge set in real time.

### Dining Sets

| Control | Effect |
|---------|--------|
| Library | Path to dining library `.blend` |
| Table | Dining table model (14 options) |
| Chair | Chair model (16 options) |
| Chairs | 2, 4, 6, or 8 chairs |
| Arrangement | Radial or Rect |
| Tablecloth | Checkbox — adds a cloth-simulated tablecloth |
| Cloth Shape | Rectangular or Round |
| Overhang | How far the cloth drapes past each table edge (default 0.30 m / ~1 ft) |
| Gap | Distance between table edge and chair front |
| **Build Dining Set** | Places the set |

#### Tablecloth simulation

When **Tablecloth** is checked:

- A plane (50×50 = 2500 faces) is created ~30 cm above the table top and parented to the set root.
- A **Cloth** modifier is added (cotton-weight settings, collision enabled).
- A **Subdivision Surface** modifier (Catmull-Clark, level 2) is added after the Cloth modifier to smooth the draped result.
- A **Collision** modifier is added to every table mesh so the cloth lands correctly.

To run the simulation: go to **frame 1** in the Timeline and press **Space**. Let it run until the cloth settles (usually 50–100 frames). You can then stop playback and optionally bake via the Cloth modifier's **Bake** button.

If the cloth looks too stiff, lower `Bending Stiffness` in the Cloth modifier. If it falls through the table, increase `Distance Min` in **Cloth → Collisions**.

---

## How it works

### Appending from library

`append_named_object()` in `utils/library_utils.py` loads a named collection from a library `.blend`, keeps only the target root object and its full hierarchy, and removes everything else. The root is linked to the scene collection with `matrix_world` already populated.

### Set root empty

Every **Build** operator creates a named empty as the set root and parents all pieces to it. Moving, rotating, or scaling the root moves the whole set. The root stores gap values as custom properties so the live-repositioning functions can read them back.

### Chair placement math

`compute_chair_placements()` / `compute_dining_chair_placements()` return a list of position dicts for each chair:

- **RADIAL** — chairs distributed evenly around the table's bounding radius at distance `table_radius + gap − chair_inward`.
- **RECT** — chairs placed on front and back long edges. For dining, 2, 3, or 4 chairs per side are spread evenly across 75% of the table half-width.

Each chair stores `afr_type`, `afr_angle`, `afr_dir_y`, `afr_x_offset`, and `afr_table_center_y` as custom properties so the **Gap** slider can reposition them without rebuilding.

#### Off-center table origins (dining)

Dining table meshes in the AFR library don't always have their geometry centered on the object origin. The dining builder computes the bounding box center (`center_x`, `center_y`) of each table and offsets all chair positions by it, so chairs are always symmetric around the actual table surface regardless of where the origin sits.

### Lounge set placement

All Tulum lounge pieces share a common local origin at `(0, 0, 0)` in the library. Their geometry is authored so that placing every piece at the same world position produces the correct set layout automatically — **no rotation or position offset is needed**.

- Coffee table → set root origin, unchanged.
- Sofa → library position; `sofa_gap` adds a Y delta.
- Chairs → library position; left chair is a linked duplicate with `scale.x = −1` (mirror, no rotation).
- End table → tracks sofa Y delta; library geometry positions it beside the sofa arm.
- Lamp / Accent → placed so their natural Y aligns behind the sofa.

### Live repositioning

Gap/spacing sliders call `reposition_chairs()` or `reposition_lounge_set()` on every change. These read role/type tags from each child and update only the relevant location component (X stays fixed for RECT chairs; only Y changes with gap).

---

## Development

### File locations

| Purpose | Path |
|---------|------|
| Dev source | `C:\Users\Carl\afr-cafe-builder\afr_furniture_builder\` |
| Installed (Blender loads from here) | `C:\Users\Carl\AppData\Roaming\Blender Foundation\Blender\5.0\scripts\addons\afr_furniture_builder\` |

After editing the dev source, copy changed files to the installed path, then hot-reload in Blender.

### Hot-reload script

Run this in Blender's **Text Editor → Run Script**:

```python
import bpy, sys
addon = "afr_furniture_builder"
for m in [k for k in sys.modules if k == addon or k.startswith(addon + ".")]:
    del sys.modules[m]
bpy.ops.preferences.addon_disable(module=addon)
bpy.ops.preferences.addon_enable(module=addon)
```

### Project structure

```
afr_furniture_builder/
├── __init__.py                    # bl_info (v0.4.0), register/unregister,
│                                  # loads/unloads branding icons
├── _afr_logo_cache.png            # Bundled AFR logo (white bg stripped at runtime)
├── operators/
│   ├── __init__.py
│   ├── build_set.py               # Cafe set builder
│   ├── build_bar_set.py           # High-seating set builder
│   ├── build_lounge_set.py        # Lounge set builder
│   └── build_dining_set.py        # Dining set builder + tablecloth helper
├── panels/
│   ├── __init__.py
│   ├── header_panel.py            # Logo-only header (bl_order=0, HIDE_HEADER)
│   ├── cafe_panel.py              # Cafe UI + CafeSettings (bl_order=1)
│   ├── bar_panel.py               # High-seating UI + BarSettings (bl_order=2)
│   ├── lounge_panel.py            # Lounge UI + LoungeSettings (bl_order=3)
│   └── dining_panel.py            # Dining UI + DiningSettings (bl_order=4)
└── utils/
    ├── branding.py                # AFR logo fetch, white-bg removal,
    │                              # pixel-art category icons (cafe/bar/lounge/dining)
    └── library_utils.py           # append_named_object, duplicate_hierarchy,
                                   # get_obj_bounds_xy, get_obj_max_z,
                                   # compute_chair_placements,
                                   # compute_dining_chair_placements,
                                   # reposition_chairs, reposition_lounge_set,
                                   # find_*_set_root functions,
                                   # all item lists and library path constants
```

### Adding a new furniture category

1. Add `MY_LIBRARY_PATH`, `MY_TABLE_ITEMS`, `MY_CHAIR_ITEMS` constants to `library_utils.py`.
2. Add `find_my_set_root()` to `library_utils.py`.
3. Create `operators/build_my_set.py` modelled on `build_dining_set.py`.
4. Create `panels/my_panel.py` modelled on `dining_panel.py`; set `bl_order` to the next integer.
5. Register both in `operators/__init__.py` and `panels/__init__.py`.
6. Copy changed files to the installed path and hot-reload.
