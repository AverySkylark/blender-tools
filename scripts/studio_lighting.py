import bpy, traceback
from mathutils import Vector
try:
    scn = bpy.context.scene
    col = bpy.data.collections.get('Collection') or scn.collection
    for o in list(bpy.data.objects):
        if o.name.startswith(('PandaLight_', 'PandaFloor')):
            bpy.data.objects.remove(o, do_unlink=True)
    m = bpy.data.objects.get('Mesh')
    if m:
        for p in m.data.polygons:
            p.use_smooth = True
    fm = bpy.data.materials.get('Panda_Floor') or bpy.data.materials.new('Panda_Floor')
    if fm.node_tree is None:
        fm.use_nodes = True
    b = [n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
    if b:
        b[0].inputs['Base Color'].default_value = (0.55, 0.55, 0.56, 1)
        b[0].inputs['Roughness'].default_value = 0.8
    me = bpy.data.meshes.new('PandaFloor')
    me.from_pydata([(-15, -15, 0), (15, -15, 0), (15, 15, 0), (-15, 15, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('PandaFloor', me)
    col.objects.link(fl)
    me.materials.append(fm)
    old = bpy.data.objects.get('Light')
    if old:
        old.hide_render = True
        old.hide_viewport = True
    tgt = Vector((0, 0, 1.0))
    for name, loc, en, sz in [('PandaLight_Key', (3.0, -4.0, 4.5), 900, 3.0),
                              ('PandaLight_Fill', (-4.5, -3.0, 2.5), 300, 4.0),
                              ('PandaLight_Rim', (0.5, 4.5, 4.0), 500, 2.5)]:
        ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, 'AREA')
        ld.energy = en
        ld.size = sz
        lo = bpy.data.objects.new(name, ld)
        col.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (tgt - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    w = scn.world or bpy.data.worlds.new('World')
    scn.world = w
    if w.node_tree is None:
        w.use_nodes = True
    bg = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND']
    if bg:
        bg[0].inputs[0].default_value = (0.75, 0.75, 0.77, 1)
        bg[0].inputs[1].default_value = 0.6
    cam = bpy.data.objects.get('Camera')
    if cam:
        cam.animation_data_clear()
        cam.data.lens = 50
        cam.location = (0, -5.6, 1.35)
        cam.rotation_euler = (Vector((0, 0, 0.95)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scn.camera = cam
    scn.render.resolution_x = 1200
    scn.render.resolution_y = 900
    print('STUDIO OK')
except Exception:
    print('STUDIO ERROR', traceback.format_exc())
