"""Bee shading for an untextured cartoon bee mesh (one fused mesh, head at -X, wings up, ~1.1 m long).

Faces go into material slots by position (object-local coordinates): Bee_Head (with procedural
glossy eyes), Bee_Body (procedural black stripes + stinger), Bee_Wing (translucent, thin-film
sheen), Bee_Antenna.

Two ways to run:
- Headless, from a GLB (imports it, adds lights + camera, renders 3 previews, saves a NEW .blend):
      blender -b --factory-startup -P bee_shade.py -- C:\\path\\to\\bee.glb
  Outputs go next to the GLB: <name>_shaded.blend, <name>_preview_{34,side,front}.png and
  bee_shade.json (log). Never overwrites an existing .blend.
- Blender console, on a bee already in the open file (materials only: no lights, camera,
  render or save):
      TARGET="Bee"; exec(open(r"C:\\path\\to\\blender-tools\\scripts\\bee_shade.py").read())
  TARGET defaults to the active object.

Tunables (console variables on the same line): NECK_X, ANT_R, WING_E, EYE_DEG. Thresholds are
in the mesh's own units and fit the Krea bee (bee.glb, 23 Nov 2026); re-measure for other meshes.
Safe to re-run: materials are rebuilt by name.
"""
import bpy, json, math, os, sys, traceback
from mathutils import Vector

HEADLESS = globals().get("HEADLESS", bpy.app.background)  # override only for testing console mode
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = globals().get("GLB", _argv[0] if _argv else None)
TARGET = globals().get("TARGET")
NECK_X = globals().get("NECK_X", -0.27)     # faces with x below this are head
ANT_Z = globals().get("ANT_Z", -0.01)       # head vertices below this define the head centre
ANT_R = globals().get("ANT_R", 0.215)       # head faces farther than this from head centre (and above it) are antennae
WING_E = globals().get("WING_E", 1.10)      # faces outside the body ellipsoid by this factor (and above z=0) are wings
EYE_DEG = globals().get("EYE_DEG", 22.0)    # eye angular radius
# body ellipsoid (centre, semi-axes) measured from the mesh's X profile
BODY_C, BODY_R = Vector((0.07, 0.0, -0.18)), Vector((0.37, 0.30, 0.30))
YELLOW = (1.0, 0.42, 0.0)
BLACK = (0.012, 0.010, 0.008)
log = {}


def principled(name, color, rough, **extra):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    for k, v in extra.items():
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = v
        else:
            log.setdefault("missing_inputs", []).append(k)
    return m, bsdf


def add_stripes(body, bsdf):
    """Black bands along X via a constant colour ramp; the last band covers the stinger."""
    nt = body.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.30
    mr.inputs["From Max"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    stops = [(0.00, YELLOW), (0.30, BLACK), (0.42, YELLOW), (0.56, BLACK), (0.68, YELLOW), (0.80, BLACK)]
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    els[1].position, els[1].color = stops[1][0], (*stops[1][1], 1)
    for pos, col in stops[2:]:
        els.new(pos).color = (*col, 1)
    for i, n in enumerate((tc, sep, mr, ramp)):
        n.location = (-1000 + i * 230, 0)
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


def add_eyes(head, hc, eye_dirs, cos_eye):
    """Mix glossy black into the head shader where the direction from the head centre is
    within EYE_DEG of an eye direction (smooth edge, no face steps)."""
    nt = head.node_tree
    hb = nt.nodes["Principled BSDF"]
    hout = nt.nodes["Material Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = hc
    nrm = nt.nodes.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
    nt.links.new(tc.outputs["Object"], sub.inputs[0])
    nt.links.new(sub.outputs[0], nrm.inputs[0])
    dots = []
    for ed in eye_dirs:
        dn = nt.nodes.new("ShaderNodeVectorMath"); dn.operation = 'DOT_PRODUCT'
        dn.inputs[1].default_value = ed
        nt.links.new(nrm.outputs[0], dn.inputs[0])
        dots.append(dn)
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'
    nt.links.new(dots[0].outputs["Value"], mx.inputs[0])
    nt.links.new(dots[1].outputs["Value"], mx.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs["From Min"].default_value = cos_eye - 0.006
    mr.inputs["From Max"].default_value = cos_eye + 0.006
    nt.links.new(mx.outputs[0], mr.inputs["Value"])
    eb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    eb.inputs["Base Color"].default_value = (0.005, 0.005, 0.006, 1)
    eb.inputs["Roughness"].default_value = 0.04
    eb.inputs["Coat Weight"].default_value = 1.0
    eb.inputs["Coat Roughness"].default_value = 0.02
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], mix.inputs[0])
    nt.links.new(hb.outputs[0], mix.inputs[1])
    nt.links.new(eb.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], hout.inputs[0])
    for i, n in enumerate((tc, sub, nrm, dots[0], mx, mr, mix)):
        n.location = (-1200 + i * 200, 400)
    dots[1].location = (-600, 250); eb.location = (-400, -400); hout.location = (300, 400)


def shade(ob):
    me = ob.data
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

    body, bb = principled("Bee_Body", YELLOW, 0.5, **{"Sheen Weight": 0.25, "Sheen Roughness": 0.5})
    add_stripes(body, bb)
    head, _ = principled("Bee_Head", YELLOW, 0.5, **{"Sheen Weight": 0.25, "Sheen Roughness": 0.5})
    ant, _ = principled("Bee_Antenna", BLACK, 0.35)
    wing, _ = principled("Bee_Wing", (0.75, 0.88, 1.0), 0.08,
                         **{"Alpha": 0.22, "Thin Film Thickness": 450.0, "Thin Film IOR": 1.4})
    if hasattr(wing, "surface_render_method"):
        wing.surface_render_method = 'BLENDED'
    wing.use_backface_culling = False

    me.materials.clear()
    slots = {}
    for m in (body, head, ant, wing):
        me.materials.append(m)
        slots[m.name] = len(me.materials) - 1

    # head centre from head vertices below the antenna line; centre one radius behind the face
    hv = [v.co for v in me.vertices if v.co.x < NECK_X and v.co.z < ANT_Z]
    if not hv:
        raise ValueError(f"No head vertices with x < {NECK_X}; is the head at -X?")
    hmin = Vector([min(c[i] for c in hv) for i in range(3)])
    hmax = Vector([max(c[i] for c in hv) for i in range(3)])
    hc = (hmin + hmax) / 2
    hc.x = hmin.x + (hmax.z - hmin.z) / 2
    log["head_centre"] = list(hc)
    eye_dirs = [Vector((-0.80, s * 0.50, 0.30)).normalized() for s in (1, -1)]
    add_eyes(head, hc, eye_dirs, math.cos(math.radians(EYE_DEG)))

    counts = {k: 0 for k in slots}
    idx = []
    for p in me.polygons:
        c = p.center
        q = c - BODY_C
        e = (q.x / BODY_R.x) ** 2 + (q.y / BODY_R.y) ** 2 + (q.z / BODY_R.z) ** 2
        if c.z > 0.0 and NECK_X - 0.06 < c.x < 0.35 and e > WING_E:
            k = "Bee_Wing"
        elif c.x < NECK_X and c.z > hc.z and (c - hc).length > ANT_R:
            k = "Bee_Antenna"
        elif c.x < NECK_X:
            k = "Bee_Head"
        else:
            k = "Bee_Body"
        counts[k] += 1
        idx.append(slots[k])
    me.polygons.foreach_set("material_index", idx)
    log["face_counts"] = counts
    return counts


def preview_scene_and_render(out_dir, stem):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1024, 1024
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    w = bpy.data.worlds.new("Bee_World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.8, 0.85, 1.0, 1)
    bg.inputs[1].default_value = 0.6

    for name, loc, energy, size in [("Key", (-1.6, -2.0, 2.0), 250, 1.5),
                                    ("Fill", (2.0, -1.5, 0.5), 80, 2.0),
                                    ("Rim", (1.0, 2.0, 1.8), 150, 1.0)]:
        L = bpy.data.lights.new(name, 'AREA')
        L.energy, L.size = energy, size
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, -0.1)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = Vector((0, 0, -0.05))
    shots = {"side": Vector((0, -2.7, 0.15)), "front": Vector((-2.7, -0.3, 0.3)), "34": Vector((-1.7, -2.2, 0.9))}
    for name, loc in shots.items():   # 3/4 last, so the saved camera keeps that view
        cam.location = loc
        cam.rotation_euler = (target - loc).to_track_quat('-Z', 'Y').to_euler()
        path = os.path.join(out_dir, f"{stem}_preview_{name}.png")
        if os.path.exists(path):
            raise RuntimeError(f"{path} exists; not overwriting.")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)


try:
    log["version"] = bpy.app.version_string
    if HEADLESS:
        if not GLB or not os.path.isfile(GLB):
            raise ValueError(f"Pass the GLB path after '--' (got {GLB!r})")
        out_dir = os.path.dirname(os.path.abspath(GLB))
        stem = os.path.splitext(os.path.basename(GLB))[0]
        blend = os.path.join(out_dir, stem + "_shaded.blend")
        if os.path.exists(blend):
            raise RuntimeError(f"{blend} exists; not overwriting. Rename or move it first.")
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=GLB)
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        if len(meshes) != 1:
            raise ValueError(f"Expected one fused mesh in the GLB, found {len(meshes)}")
        meshes[0].name = "Bee"
        shade(meshes[0])
        preview_scene_and_render(out_dir, stem)
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        log["saved"] = blend
        print("bee_shade OK", blend)
    else:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        ob = bpy.data.objects.get(TARGET) if TARGET else bpy.context.active_object
        if ob is None or ob.type != 'MESH':
            raise ValueError(f"No mesh to shade (TARGET={TARGET!r}, active={bpy.context.active_object!r})")
        print("bee_shade OK", ob.name, shade(ob))
except Exception:
    log["error"] = traceback.format_exc()
    print("bee_shade ERROR", log["error"])
if HEADLESS and GLB and os.path.isdir(os.path.dirname(os.path.abspath(GLB))):
    with open(os.path.join(os.path.dirname(os.path.abspath(GLB)), "bee_shade.json"), "w") as f:
        json.dump(log, f, indent=1)
