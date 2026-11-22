import bpy, traceback
from mathutils import Vector
from mathutils.geometry import intersect_point_line
try:
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    print('Blender', bpy.app.version_string)
    me = bpy.data.objects['Mesh']
    # clean previous run
    old = bpy.data.objects.get('PandaRig')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    for md in list(me.modifiers):
        if md.type == 'ARMATURE':
            me.modifiers.remove(md)
    me.vertex_groups.clear()
    me.parent = None
    mw = me.matrix_world.copy()
    V = [mw @ v.co for v in me.data.vertices]
    maxx = max(v.x for v in V)
    maxz = max(v.z for v in V)

    def avg(pts):
        s = Vector((0, 0, 0))
        for p in pts:
            s += p
        return s / max(len(pts), 1)

    def arm_pts(sign):
        tip = avg([v for v in V if v.x * sign > maxx - 0.06])
        sh = avg([v for v in V if 0.36 < v.x * sign < 0.44 and v.z > 0.7])
        return sh, tip

    shR, tipR = arm_pts(-1)
    shL, tipL = arm_pts(1)

    def leg_pts(sign):
        pts = [v for v in V if v.z < 0.35 and v.x * sign > 0.02]
        c = avg(pts)
        return Vector((c.x, 0, 0.5)), Vector((c.x, c.y, 0.1))

    hipL, ankL = leg_pts(1)
    hipR, ankR = leg_pts(-1)
    print('shoulderL', tuple(round(a, 2) for a in shL), 'tipL', tuple(round(a, 2) for a in tipL))
    print('hipL', tuple(round(a, 2) for a in hipL), 'ankL', tuple(round(a, 2) for a in ankL), 'top', round(maxz, 2))
    neck_z = shL.z - 0.06

    arm = bpy.data.armatures.new('PandaRig')
    rig = bpy.data.objects.new('PandaRig', arm)
    me.users_collection[0].objects.link(rig)
    arm.display_type = 'STICK'
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones

    def bone(name, h, t, parent=None, connect=False):
        b = eb.new(name)
        b.head = h
        b.tail = t
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        return b

    bone('Hips', (0, 0, 0.5), (0, 0, 0.8))
    bone('Spine', (0, 0, 0.8), (0, 0, neck_z), 'Hips', True)
    bone('Head', (0, 0, neck_z), (0, 0, maxz - 0.05), 'Spine', True)
    for side, sh, tip in (('L', shL, tipL), ('R', shR, tipR)):
        sh2 = Vector((sh.x, 0, sh.z))
        tip2 = Vector((tip.x, 0, tip.z))
        el = (sh2 + tip2) / 2
        bone('UpperArm.' + side, sh2, el, 'Spine')
        bone('LowerArm.' + side, el, tip2, 'UpperArm.' + side, True)
    for side, hp, ak in (('L', hipL, ankL), ('R', hipR, ankR)):
        kn = (hp + ak) / 2 + Vector((0, -0.02, 0))
        bone('Thigh.' + side, hp, kn, 'Hips')
        bone('Shin.' + side, kn, ak, 'Thigh.' + side, True)
    bpy.ops.object.mode_set(mode='OBJECT')

    # bind with automatic weights
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    me.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except Exception as ex:
        print('auto weights raised', ex)
    n = len(me.data.vertices)
    weighted = sum(1 for v in me.data.vertices if any(g.weight > 0 for g in v.groups))
    print('auto weighted', weighted, 'of', n)
    if weighted < 0.95 * n:
        print('falling back to distance weights')
        for vg in list(me.vertex_groups):
            me.vertex_groups.remove(vg)
        segs = [(b.name, rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local) for b in arm.bones]
        groups = {nm: me.vertex_groups.new(name=nm) for nm, h, t in segs}
        for i, p in enumerate(V):
            ws = []
            for nm, h, t in segs:
                q, f = intersect_point_line(p, h, t)
                f = min(max(f, 0.0), 1.0)
                d = (p - (h + (t - h) * f)).length
                ws.append((1.0 / (d ** 6 + 1e-6), nm))
            ws.sort(reverse=True)
            top = ws[:2]
            s = sum(w for w, nm in top)
            for w, nm in top:
                groups[nm].add([i], w / s, 'REPLACE')
        if not any(md.type == 'ARMATURE' for md in me.modifiers):
            am = me.modifiers.new('Armature', 'ARMATURE')
            am.object = rig
        if me.parent != rig:
            me.parent = rig
            me.matrix_parent_inverse = rig.matrix_world.inverted()
    # keep Armature first in the stack
    am = [md for md in me.modifiers if md.type == 'ARMATURE'][0]
    try:
        me.modifiers.move(list(me.modifiers).index(am), 0)
    except Exception as ex:
        print('move skipped', ex)
    print('modifiers', [m.name for m in me.modifiers])
    print('RIG OK', [b.name for b in arm.bones])
except Exception:
    print('RIG ERROR', traceback.format_exc())
