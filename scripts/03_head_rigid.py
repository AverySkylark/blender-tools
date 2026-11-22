import bpy, traceback
try:
    me = bpy.data.objects['Mesh']
    rig = bpy.data.objects['PandaRig']
    nz = rig.data.bones['Head'].head_local.z
    mw = me.matrix_world
    gH = me.vertex_groups['Head']
    gS = me.vertex_groups['Spine']
    n = 0
    for v in me.data.vertices:
        p = mw @ v.co
        if p.z < nz - 0.06 or (abs(p.x) > 0.38 and p.z < nz + 0.2):
            continue
        t = min(max((p.z - (nz - 0.06)) / 0.14, 0.0), 1.0)
        for g in list(v.groups):
            me.vertex_groups[g.group].remove([v.index])
        if t > 0:
            gH.add([v.index], t, 'REPLACE')
        if t < 1:
            gS.add([v.index], 1 - t, 'REPLACE')
        n += 1
    print('HEADFIX OK', n, 'verts, neck', round(nz, 2))
except Exception:
    print('HEADFIX ERROR', traceback.format_exc())
