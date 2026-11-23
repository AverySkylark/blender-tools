# Blender Tools

Python scripts for Blender 5.2 (EEVEE) that set up, rig and outline AI-generated characters. They were first built for the panda (`panda.blend`, a Rodin V2.5 Fast GLB from Krea) on 23 Nov 2026.

## Running a script

From the Scripting tab's Python console:

```python
exec(open(r"C:\path\to\blender-tools\scripts\02_seam_weight_match.py").read())
```

If Blender can't read the folder, run `python make_console_line.py <script>` and paste the single line it prints.

Set options as console variables on the same line first, e.g. `TARGET="Bird"; RAD=0.02; exec(...)`. Every script is safe to re-run and prints `... OK` or `... ERROR <traceback>`.

## Scripts

| Script | What it does |
|---|---|
| `studio_lighting.py` | Grey floor, 3 area lights (key, fill, rim), soft world, 50 mm camera framing, 1200×900. Hides the default `Light` (doesn't delete it). Smooth-shades `Mesh`. |
| `lineart_outline.py` | Cartoon ink outlines (Grease Pencil Line Art) plus a non-destructive `SeamWeld` modifier so texture seams don't draw as cracks. |
| `01_rig_build_and_bind.py` | Builds `PandaRig` (11 bones: Hips, Spine, Head, UpperArm/LowerArm L/R, Thigh/Shin L/R) from measurements of the mesh, then binds with automatic weights (falls back to distance weights if auto fails). |
| `02_seam_weight_match.py` | Gives the two sides of every texture seam identical weights. **Always run this last.** |
| `03_head_rigid.py` | Makes the whole head move as one piece, blending into the body at the neck. Stops the muzzle crumpling when the head turns. |
| `04_orphan_verts_and_reset.py` | Assigns any unweighted points (e.g. fingertips) to the nearest bone, then resets the pose. |
| `05_limb_weights_and_smooth.py` | Sets arm and leg weights by position along each bone (soft shoulder, elbow, hip and knee), keeps the belly centre with the hips, then smooths all body weights (head excluded). |
| `bee_shade.py` | Bee materials for the untextured Krea bee (one fused mesh, head at −X): yellow body with black stripes and stinger, glossy procedural eyes, black antennae, translucent wings. Parts are picked by position, as the mesh has no UVs. Headless from a GLB (`blender -b --factory-startup -P bee_shade.py -- bee.glb` adds lights and camera, renders 3 previews, saves `<name>_shaded.blend` next to the GLB, never overwrites) or from the console on the active object (materials only). |
| `example_metaball_panda.py` | The first hand-built panda from metaballs. Reference only. |
| `make_console_line.py` | Turns a script into a one-line `exec(...)` for the console. Runs on your PC with Python, not inside Blender. |

## Rigging run order

1. Import the GLB. Delete the default cube, because the import lands inside it. Stand the model on the floor.
2. `studio_lighting.py` (optional)
3. `01_rig_build_and_bind.py`
4. `03_head_rigid.py`
5. `04_orphan_verts_and_reset.py`
6. `05_limb_weights_and_smooth.py`
7. `02_seam_weight_match.py`
8. `lineart_outline.py` (optional)

Test with a pose (raise an arm, turn the head, bend an elbow, splay the legs) and render before saving.

## Panda-specific assumptions (generalise before reuse)

- The mesh object is called `Mesh`, at its imported scale (about 1.9 m tall), feet at z=0 and facing −Y.
- Two arms out to the sides, two legs, one head. Thresholds are in metres and fit panda proportions: shoulder slab x 0.36–0.44, arm radius 0.15, paw beyond x 0.62, legs below z 0.56, neck 6 cm below shoulder height.
- **The kookaburra needs new versions:** wings instead of arms, a tail, a beak, and a perch bone that stays still.

## Lessons learned

**Krea's Blender bridge (free)**
- It can inspect the scene, take preview renders, switch workspaces and move whole objects.
- It can't run scripts or pose bones. Use the console for those.
- Its `appId` changes whenever the file is reopened, so call `list_desktop_apps` again.

**Running Blender headless (Microsoft Store install)**
- Windows blocks running `blender.exe` from `WindowsApps` directly. Use the app alias `%LOCALAPPDATA%\Microsoft\WindowsApps\blender-launcher.exe` with the usual `-b -P script.py -- args`.
- The alias doesn't pass Blender's printed output back, so have scripts write a log file.
- A headless run is a separate Blender; it leaves the file open in your Blender alone.

**Credits**
- Get a quote (preflight) before every generation; quotes are free.
- Rodin V2.5 Fast cost 74 credits, about 1.5% of the monthly plan. Meshy 7.1 cost 889.

**Controlling Blender from Claude**
- Never use "open application" while Blender is already running, because it launches a second copy. Ask the user to click the window instead.
- Keyboard input goes to whichever area is under the mouse, so always click the console before typing.
- Floating windows, such as the render window, can cover the console. Move them aside first.

**AI meshes**
- They are one fused mesh, split along texture seams. Mesh-only generations avoid the seams but have no colour.
- Use reference images with limbs apart, wings slightly out and the beak open.

**Weights**
- Blender's automatic weights look fine at rest but fail in poses: paws left behind, muzzle crumpled, belly torn, shoulders creased.
- Position-based weights, smoothing and a final seam match fix all of these.

**Line Art**
- Intersection lines draw stray cracks on AI meshes. Seams draw as cracks too, so add a Weld modifier.
- Outlines are invisible on black fur.

**Saving**
- Save often. Reopening the file loses anything since the last save. That's how the first Line Art setup was lost.
