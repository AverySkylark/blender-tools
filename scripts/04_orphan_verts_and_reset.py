import bpy, traceback
from mathutils.geometry import intersect_point_line
try:
    me = bpy.data.objects['Mesh']
    rig = bpy.data.objects['PandaRig']
    mw = me.matrix_world
    segs = [(b.name, b.head_local, b.tail_local) for b in rig.data.bones]
    n = 0
    for v in me.data.vertices:
        if any(g.weight > 0.001 for g in v.groups):
            continue
        p = mw @ v.co
        best = None
        for nm, h, t in segs:
            q, f = intersect_point_line(p, h, t)
            f = min(max(f, 0.0), 1.0)
            d = (p - (h + (t - h) * f)).length
            if best is None or d < best[0]:
                best = (d, nm)
        me.vertex_groups[best[1]].add([v.index], 1.0, 'REPLACE')
        n += 1
    for b in rig.pose.bones:
        b.rotation_euler = (0, 0, 0)
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.view_layer.update()
    print('ORPHANFIX OK', n, 'verts assigned, pose reset')
except Exception:
    print('ORPHANFIX ERROR', traceback.format_exc())
