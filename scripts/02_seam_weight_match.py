import bpy, traceback
try:
    me = bpy.data.objects['Mesh']
    vs = me.data.vertices
    names = [g.name for g in me.vertex_groups]
    buckets = {}
    for v in vs:
        k = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
        buckets.setdefault(k, []).append(v.index)
    fixed = 0
    for idxs in buckets.values():
        if len(idxs) < 2:
            continue
        acc = {}
        for i in idxs:
            for g in vs[i].groups:
                acc[g.group] = acc.get(g.group, 0.0) + g.weight
        if not acc:
            continue
        for gi in acc:
            acc[gi] /= len(idxs)
        for i in idxs:
            for g in list(vs[i].groups):
                if g.group not in acc:
                    me.vertex_groups[g.group].remove([i])
            for gi, w in acc.items():
                me.vertex_groups[gi].add([i], w, 'REPLACE')
        fixed += 1
    print('SEAMFIX OK', fixed, 'seam points averaged')
except Exception:
    print('SEAMFIX ERROR', traceback.format_exc())
