# Cartoon ink outlines via Grease Pencil Line Art (Blender 5.2).
# Set TARGET in the console first if the mesh isn't called 'Mesh'.
import bpy, traceback
try:
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    name = globals().get('TARGET', 'Mesh')
    m = bpy.data.objects[name]
    # Close texture seams so Line Art doesn't draw them as cracks (non-destructive)
    w = m.modifiers.get('SeamWeld') or m.modifiers.new('SeamWeld', 'WELD')
    w.merge_threshold = 0.0005
    for o in list(bpy.data.objects):
        if o.name.startswith('LineArt_' + name):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = m
    m.select_set(True)
    bpy.ops.object.grease_pencil_add(type='LINEART_OBJECT')
    gp = bpy.context.view_layer.objects.active
    gp.name = 'LineArt_' + name
    # NB: in 5.2 the modifier type is 'LINEART', not 'GREASE_PENCIL_LINEART'
    md = [x for x in gp.modifiers if x.type == 'LINEART'][0]
    md.source_type = 'OBJECT'
    md.source_object = m
    md.use_contour = True
    md.use_intersection = False   # AI meshes self-intersect -> stray lines
    md.use_crease = False
    md.use_loose = False
    md.use_material = False
    md.use_edge_mark = False
    md.silhouette_filtering = 'NONE'  # 'GROUP' = outer silhouette only (fallback if seams still show)
    md.radius = globals().get('RAD', 0.015)
    md.smooth_tolerance = 0.2
    print('LINEART OK', gp.name, md.radius)
except Exception:
    print('LINEART ERROR', traceback.format_exc())
