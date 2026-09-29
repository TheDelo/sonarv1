"""
Sonar Mapper — point cloud to mesh (Blender).

The mesh-building core (build_mesh) is extracted from the TIPE report,
Annexe 3 (comments translated to English, logic unchanged). CSV loading
was added to connect this stage to the rest of the pipeline described in
the README — it was not part of the original report code.

Run inside Blender:
    blender --python import_points.py -- data/sample_log.txt

If no CSV path is given, falls back to the original 3-point example from
the report.
"""

import sys
import csv
import math

import bpy
import bmesh


def load_points_from_csv(path):
    """Read lat,lon,distance rows and return a list of (x, y, z) tuples.

    lat/lon are converted to a local flat approximation in meters,
    relative to the first fix; distance (logged in cm, positive downward)
    becomes z. This is a simple equirectangular approximation, adequate
    for the small survey areas used here — not intended for large-scale
    mapping.
    """
    points = []
    origin = None
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            lat, lon, dist = (float(v) for v in row[:3])
            if origin is None:
                origin = (lat, lon)
            lat0, lon0 = origin
            meters_per_deg_lat = 111_320.0
            meters_per_deg_lon = 111_320.0 * math.cos(math.radians(lat0))
            x = (lon - lon0) * meters_per_deg_lon
            y = (lat - lat0) * meters_per_deg_lat
            z = -dist / 100.0  # cm to m, downward
            points.append((x, y, z))
    return points


# Example point list (original report demo, Annexe 3)
DEFAULT_POINTS = [
    (1.0, 2.0, 3.0),
    (4.0, 5.0, 6.0),
    (7.0, 8.0, 9.0),
]


def build_mesh(points, name="SonarPointCloud"):
    # Create a new mesh object
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Link the object to the scene
    bpy.context.collection.objects.link(obj)

    # Build the bmesh to add vertices
    bm = bmesh.new()
    for coord in points:
        bm.verts.new(coord)

    # Finalize the bmesh
    bm.to_mesh(mesh)
    bm.free()

    for coord in points:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=coord)


def get_cli_csv_path():
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        if args:
            return args[0]
    return None


if __name__ == "__main__":
    csv_path = get_cli_csv_path()
    pts = load_points_from_csv(csv_path) if csv_path else DEFAULT_POINTS
    build_mesh(pts)
