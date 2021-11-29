from stl import mesh
import numpy as np
import os


def export_stl(project_folder, triangles_a, object_type):
    object_type_d = {"Terrain": "terrain.stl",
                     "Vegetation": "vegetation.stl",
                     "Target_Buildings": "target_buildings.stl",
                     "Surrounding_Buildings": "surrounding_buildings.stl",
                     "Static": "static_objects.stl",
                     "Buildings": "all_buildings.stl",
                     "Windows": "windows.stl",
                     "Windows+TB": "windows+tb.stl"}

    if "DigitalTwin" in project_folder:
        export_fp = os.path.join(project_folder, "STLfiles")
    else:
        export_fp = os.path.join(project_folder, "DigitalTwin", "STLfiles")

    num_triangles = len(triangles_a)
    data = np.zeros(num_triangles, dtype=mesh.Mesh.dtype)
    for i, j in enumerate(triangles_a):
        data["vectors"][i] = np.array([j[0], j[1], j[2]])
    m = mesh.Mesh(data)

    for key, value in object_type_d.items():
        if object_type == key:
            m.save(os.path.join(export_fp, value))
    # todo use logging package instead of print("%s type exported to stl." % type)


def import_stl(mesh_file):
    triangles_meshed = np.empty(len(mesh_file), dtype=object)
    for position, data in enumerate(mesh_file.data):
        data_new = data[1].tolist()
        data_new.append(data[1][0].tolist())
        data_new_a = np.array(data_new)
        triangles_meshed[position] = data_new_a
    return triangles_meshed

"""
project_folder = r"G:\Shared drives\04_Sales_and_Operations\03_Operations\Twin_Hatten\Stadtwerke-Buchholz"
stl_folder = os.path.join(project_folder, 'DigitalTwin', 'STLfiles')
tree_mesh_list = []
for stl_file in os.listdir(stl_folder):
    # if 'building' in stl_file:
    print(stl_file)
    tree_mesh = mesh.Mesh.from_file(os.path.join(stl_folder, stl_file))
    tree_mesh_a = import_stl(tree_mesh)
    tree_mesh_list.append(tree_mesh_a)

all_trees = np.concatenate(tree_mesh_list)
export_stl(project_folder, all_trees, 'Vegetation')

building_list = []
for stl_file in os.listdir(stl_folder):
    if 'building' in stl_file:
        print(stl_file)
        building_mesh = mesh.Mesh.from_file(os.path.join(stl_folder, stl_file))
        building_mesh_a = import_stl(building_mesh)
        building_list.append(building_mesh_a)

all_buildings = np.concatenate(building_list)
export_stl(project_folder, all_buildings, "Static")
export_stl(stl_folder, all_buildings, 'all_buildings')"""


# 27/05 15:24
