import bpy, traceback
from mathutils.geometry import intersect_point_line
try:
    me = bpy.data.objects['Mesh']
    rig = bpy.data.objects['PandaRig']
    B = rig.data.bones
    mw = me.matrix_world
    VG = me.vertex_groups
    nz = B['Head'].head_local.z

    def cl(x):
        return min(max(x, 0.0), 1.0)

    def setw(i, ws):
        for g in list(me.data.vertices[i].groups):
            VG[g.group].remove([i])
        for nm, w in ws.items():
            if w > 0.001:
                VG[nm].add([i], w, 'REPLACE')

    na = nl = 0
    for v in me.data.vertices:
        p = mw @ v.co
        side = 'L' if p.x > 0 else 'R'
        sx = abs(p.x)
        # arms
        ua, la = B['UpperArm.' + side], B['LowerArm.' + side]
        sh, tip = ua.head_local, la.tail_local
        q, f = intersect_point_line(p, sh, tip)
        L = (tip - sh).length
        fc = cl(f)
        d = (p - (sh + (tip - sh) * fc)).length
        if sx > 0.3 and 0.4 < p.z < nz + 0.2 and (d < 0.15 or (f > 0.6 and sx > 0.62 and d < 0.32)):
            s = f * L
            wsp = cl((0.04 - s) / 0.1)
            t = cl((s - (L / 2 - 0.06)) / 0.12)
            setw(v.index, {'Spine': wsp, 'UpperArm.' + side: (1 - wsp) * (1 - t), 'LowerArm.' + side: (1 - wsp) * t})
            na += 1
            continue
        # legs
        if p.z < 0.56 and sx < 0.42:
            th = B['Thigh.' + side]
            k = th.tail_local.z
            wh = max(cl((p.z - 0.44) / 0.12), cl((0.16 - sx) / 0.12) * cl((p.z - 0.25) / 0.15))
            t = cl((k + 0.05 - p.z) / 0.1)
            setw(v.index, {'Hips': wh, 'Thigh.' + side: (1 - wh) * (1 - t), 'Shin.' + side: (1 - wh) * t})
            nl += 1
    bpy.context.view_layer.update()
    print('LIMBFIX OK arms', na, 'legs', nl)
except Exception:
    print('LIMBFIX ERROR', traceback.format_exc())

try:
    me = bpy.data.objects['Mesh']
    rig = bpy.data.objects['PandaRig']
    nz = rig.data.bones['Head'].head_local.z
    mw = me.matrix_world
    vs = me.data.vertices
    VG = me.vertex_groups
    nV = len(vs)
    G = len(VG)
    nb = [[] for _ in range(nV)]
    for e in me.data.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    buckets = {}
    for v in vs:
        k = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
        buckets.setdefault(k, []).append(v.index)
    for idxs in buckets.values():
        if len(idxs) > 1:
            for i in idxs:
                nb[i].extend(j for j in idxs if j != i)
    W = [[0.0] * G for _ in range(nV)]
    for v in vs:
        for g in v.groups:
            W[v.index][g.group] = g.weight
    mask = [(mw @ v.co).z < nz - 0.08 for v in vs]
    for it in range(globals().get('ITER', 10)):
        NW = [r[:] for r in W]
        for i in range(nV):
            if not mask[i] or not nb[i]:
                continue
            acc = [0.0] * G
            for j in nb[i]:
                rj = W[j]
                for k in range(G):
                    acc[k] += rj[k]
            n = len(nb[i])
            r = W[i]
            NW[i] = [0.5 * r[k] + 0.5 * acc[k] / n for k in range(G)]
        W = NW
    for k in range(G):
        VG[k].remove(list(range(nV)))
    for i in range(nV):
        s = sum(W[i])
        if s <= 0:
            continue
        for k in range(G):
            w = W[i][k] / s
            if w > 0.002:
                VG[k].add([i], w, 'REPLACE')
    bpy.context.view_layer.update()
    print('SMOOTH OK', nV, 'verts', G, 'groups')
except Exception:
    print('SMOOTH ERROR', traceback.format_exc())
