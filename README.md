# AFR Furniture Builder

A Blender add-on for placing AFR (American Furniture Rentals) furniture sets from library `.blend` files. Mirrors the Unreal Engine event-production workflow used by Majic Production Services.

**Version:** 0.2.0  
**Blender:** 3.6+  
**Panel location:** View3D → Sidebar → AFR Furniture

---

## Overview

The add-on reads furniture assets from three separate AFR library `.blend` files and places fully-parented sets in the scene. Each set is built around a root empty so the whole group can be moved together. Sliders let you fine-tune spacing live after placement.

Three builders are included:

| Tab | Library file | What it places |
|-----|-------------|----------------|
| **Cafe Sets** | `AFR Cafe Seating Furniture.blend` | Cafe table + chairs (2 or 4) |
| **High Seating** | `AFR High Seating Furniture.blend` | Bar/pub table + bar stools (2 or 4) |
| **Lounge Sets** | `AFR Lounge Furniture.blend` | Sofa + coffee table + 2 lounge chairs + optional end table, accent, and lamp |

---

## Installation

1. Zip the `afr_furniture_builder/` folder (the folder itself, not its contents).
2. In Blender: **Edit → Preferences → Add-ons → Install** → select the zip.
3. Enable **AFR Furniture Builder** in the add-on list.

The panel appears in the **N-panel** (View3D sidebar) under the **AFR Furniture** tab.

### Library file paths

Each panel has a **Library** path field at the top. Set these to wherever your AFR `.blend` library files live on disk. The defaults point to:

```
D:\Blender\Decore\AFR Furniture\AFR Cafe Seating Furniture.blend
D:\Blender\Decore\AFR Furniture\AFR High Seating Furniture.blend
D:\Blender\Decore\AFR Furniture\AFR Lounge Furniture.blend
```

---

## How it works

### Appending from library

`append_named_object()` in `utils/library_utils.py` uses `bpy.data.libraries.load()` to append an entire collection from the library file, then keeps only the target root object and its hierarchy. All other appended objects are removed. The returned root is already linked to the scene collection with `matrix_world` populated.

### Set root empty

Each **Build** operator creates a named empty as the set root and parents all pieces to it. The root stores the current gap values as custom properties (`afr_sofa_gap`, etc.) so the live-repositioning functions can read them back.

### Lounge set placement

All Tulum furniture pieces in the lounge library share a common local origin at `(0, 0, 0)`. Their mesh geometry is authored so that placing every piece at the same world point produces the correct set layout automatically — **no rotation or position offset is needed for the main pieces**.

- **Coffee table** — placed at the set root origin, library orientation unchanged.
- **Sofa** — placed at library position; `sofa_gap` slider adds a Y delta (positive = further from table).
- **Chairs** — placed at library position; `chair_gap` slider adds a Y delta. The right chair is appended directly; the left chair is a linked duplicate with `scale.x = −1` to mirror it across the Y axis (matches the Unreal version).
- **End table** — placed at library position tracking the sofa's Y delta; library geometry positions it beside the sofa arm.
- **Accent / Lamp** *(optional)* — placed so their front face aligns with the sofa's back face. Y position is computed as `sofa_max_y − piece_min_y + sofa_gap`.

### Cafe and high-seating placement

Table placed at the set origin; chairs are arranged around it using `compute_chair_placements()`:

- **RADIAL** — chairs distributed evenly around a circular/square table.
- **RECT** — chairs placed on the front and back long edges (2-top or 4-top).

Each chair stores `afr_type`, `afr_angle`, `afr_dir_y`, and `afr_table_half_d` as custom properties so the live **Gap** slider can reposition them without rebuilding.

### Live repositioning

Sliders call `reposition_lounge_set()` / `reposition_chairs()` on every change. These functions read the role or type tags from each child of the set root and update only the relevant location components, leaving X, Y, or Z alone as appropriate.

---

## Panel reference

### Cafe Sets

| Control | Effect |
|---------|--------|
| Library | Path to cafe library `.blend` |
| Table | Table model |
| Chair | Chair/stool model |
| Chairs | 2 or 4 chairs |
| Arrangement | Radial or rectangular |
| Gap | Distance between table edge and chair seat |
| **Build Cafe Set** | Places the set |

### High Seating

Same controls as Cafe Sets but draws from the bar/pub library.

### Lounge Sets

| Control | Effect |
|---------|--------|
| Library | Path to lounge library `.blend` |
| Coffee Table | Cocktail table model |
| Sofa | Sofa/loveseat model |
| Chair | Lounge chair model |
| End Table *(optional)* | Toggle + model picker |
| Accent *(optional)* | Toggle + model picker |
| Lamp *(optional)* | Toggle + model picker |
| Sofa Gap | Y shift from library position (0 = as designed) |
| Chair Gap | Y shift from library position (0 = as designed) |
| Chair Spread | X offset per chair from library position (0 = as designed) |
| **Build Lounge Set** | Places the set |

Sliders update any selected/active lounge set in real time.

---

## Development

### File locations

| Purpose | Path |
|---------|------|
| Dev source | `C:\Users\Carl\afr-cafe-builder\afr_furniture_builder\` |
| Installed (Blender loads from) | `C:\Users\Carl\AppData\Roaming\Blender Foundation\Blender\5.0\scripts\addons\afr_furniture_builder\` |

After editing the dev source, copy the changed files to the installed path and reload in Blender.

### Hot-reload during development

Run `reload.py` in Blender's **Text Editor → Run Script**. It flushes all cached modules and re-enables the add-on without restarting Blender.

```python
# reload.py — run from Blender's Text Editor
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
├── __init__.py                  # bl_info, register/unregister
├── operators/
│   ├── build_set.py             # Cafe set builder
│   ├── build_bar_set.py         # High-seating set builder
│   └── build_lounge_set.py      # Lounge set builder
├── panels/
│   ├── cafe_panel.py            # Cafe UI + CafeSettings PropertyGroup
│   ├── bar_panel.py             # High-seating UI + BarSettings PropertyGroup
│   └── lounge_panel.py          # Lounge UI + LoungeSettings PropertyGroup
└── utils/
    └── library_utils.py         # append_named_object, duplicate_hierarchy,
                                 # get_obj_bounds_xy, compute_chair_placements,
                                 # reposition_chairs, reposition_lounge_set,
                                 # all item lists and library path constants
```
