# Decisions

## 2026-11-23 · Bee shading picks parts by position
**Chose:** sort the bee's faces into material slots (head, body, antennae, wings) by where they sit, with stripes and eyes as procedural shader nodes in object space.
**Alternative:** UV-unwrap and paint a texture; or one material per loose part.
**Why:** the Krea bee is one fused mesh with no UVs, materials or loose parts. Procedural eyes and stripes give smooth edges that face-by-face assignment didn't (the first try had ragged eyes).

## 2026-11-23 · Bee script runs headless by default
**Chose:** `bee_shade.py` imports the GLB in a background Blender and saves a new `<name>_shaded.blend`; console mode only changes materials.
**Alternative:** drive the open Blender through the console with computer use.
**Why:** computer use wasn't available, and a background run can't touch the user's open, unsaved file. The console mode skips the factory reset, so running it in a live session never wipes the scene.
