import bpy, math, traceback
from mathutils import Vector, Euler
try:
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    print('Blender', bpy.app.version_string)
    scn = bpy.context.scene
    col = bpy.data.collections.get('Collection') or scn.collection
    # clean previous runs of this script
    for o in list(bpy.data.objects):
        if o.name.startswith(('PW', 'PB', 'PandaLight_', 'PandaFloor', 'PCal')):
            bpy.data.objects.remove(o, do_unlink=True)
    for d in list(bpy.data.metaballs):
        if d.users == 0:
            bpy.data.metaballs.remove(d)
    # old blocky parts replaced by metaballs
    for n in ['Panda_Body', 'Panda_Head', 'Panda_Muzzle', 'Panda_ShoulderBand', 'Panda_Arm_R', 'Panda_Arm_L',
              'Panda_Leg_R', 'Panda_Leg_L', 'Panda_Foot_R', 'Panda_Foot_L']:
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)

    def mat(name, rgb, rough):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        if m.node_tree is None:
            m.use_nodes = True
        nt = m.node_tree
        b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
        if b:
            b = b[0]
        else:
            b = nt.nodes.new('ShaderNodeBsdfPrincipled')
            out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
            nt.links.new(b.outputs[0], out.inputs[0])
        b.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
        b.inputs['Roughness'].default_value = rough
        m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1)
        return m

    WHITE = mat('Panda_White', (0.88, 0.88, 0.87), 0.55)
    BLACK = mat('Panda_Black', (0.018, 0.014, 0.014), 0.5)
    FLOOR = mat('Panda_Floor', (0.55, 0.55, 0.56), 0.8)

    # calibrate: visible radius of an isolated ball of radius 1
    mb = bpy.data.metaballs.new('PCal')
    ob = bpy.data.objects.new('PCal', mb)
    col.objects.link(ob)
    e = mb.elements.new()
    e.type = 'BALL'
    e.radius = 1.0
    bpy.context.view_layer.update()
    k = ob.dimensions.x / 2.0
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    print('calib k', round(k, 3))
    if k < 0.2 or k > 1.5:
        k = 0.6
    SH = globals().get('SHRINK', 0.92)

    def meta(name, elems, m):
        mb = bpy.data.metaballs.new(name)
        mb.resolution = 0.03
        mb.render_resolution = 0.012
        mb.threshold = 0.6
        ob = bpy.data.objects.new(name, mb)
        col.objects.link(ob)
        mb.materials.append(m)
        for co, size, rot in elems:
            e = mb.elements.new()
            e.type = 'ELLIPSOID'
            e.co = co
            e.radius = 1.0 / k
            e.size_x, e.size_y, e.size_z = size[0] * SH, size[1] * SH, size[2] * SH
            e.rotation = Euler(rot).to_quaternion()
        return ob

    Z = (0, 0, 0)
    meta('PW', [((0, 0, 0.86), (0.52, 0.45, 0.6), Z),
                ((0, 0, 1.55), (0.53, 0.48, 0.56), Z),
                ((0, -0.37, 1.42), (0.2, 0.15, 0.14), Z)], WHITE)
    meta('PB', [((0, 0, 1.13), (0.52, 0.48, 0.17), Z),
                ((0.74, 0, 0.88), (0.42, 0.11, 0.11), (0, 0.62, 0)),
                ((-0.74, 0, 0.88), (0.42, 0.11, 0.11), (0, -0.62, 0)),
                ((0.22, 0, 0.32), (0.15, 0.15, 0.3), Z),
                ((-0.22, 0, 0.32), (0.15, 0.15, 0.3), Z),
                ((0.22, -0.05, 0.09), (0.17, 0.22, 0.1), Z),
                ((-0.22, -0.05, 0.09), (0.17, 0.22, 0.1), Z)], BLACK)

    # smooth the remaining small parts
    for o in bpy.data.objects:
        if o.name.startswith('Panda_') and o.type == 'MESH':
            for p in o.data.polygons:
                p.use_smooth = True
            if not o.modifiers.get('Subd'):
                s = o.modifiers.new('Subd', 'SUBSURF')
                s.levels = 2
                s.render_levels = 2
            if o.name.startswith(('Panda_Ear_', 'Panda_EyePatch', 'Panda_Nose')):
                o.data.materials.clear()
                o.data.materials.append(BLACK)

    # floor
    me = bpy.data.meshes.new('PandaFloor')
    me.from_pydata([(-15, -15, 0), (15, -15, 0), (15, 15, 0), (-15, 15, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('PandaFloor', me)
    col.objects.link(fl)
    me.materials.append(FLOOR)

    # lights
    old = bpy.data.objects.get('Light')
    if old:
        old.hide_render = True
        old.hide_viewport = True
    tgt = Vector((0, 0, 1.1))

    def light(name, loc, energy, size):
        ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        col.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (tgt - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    light('PandaLight_Key', (3.0, -4.0, 4.5), 900, 3.0)
    light('PandaLight_Fill', (-4.5, -3.0, 2.5), 300, 4.0)
    light('PandaLight_Rim', (0.5, 4.5, 4.0), 500, 2.5)

    # world
    w = scn.world or bpy.data.worlds.new('World')
    scn.world = w
    if w.node_tree is None:
        w.use_nodes = True
    bg = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND']
    if bg:
        bg[0].inputs[0].default_value = (0.75, 0.75, 0.77, 1)
        bg[0].inputs[1].default_value = 0.6

    # camera
    cam = bpy.data.objects.get('Camera')
    if cam:
        cam.animation_data_clear()
        cam.data.lens = 50
        cam.location = (0, -8.0, 1.6)
        cam.rotation_euler = (Vector((0, 0, 1.02)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scn.camera = cam
    scn.render.resolution_x = 1200
    scn.render.resolution_y = 900
    print('PANDA OK', [o.name for o in bpy.data.objects if o.name.startswith(('PW', 'PB'))])
except Exception:
    print('PANDA ERROR', traceback.format_exc())
