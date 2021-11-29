from stl_handling import import_stl, export_stl
from stl import mesh
import os
import numpy as np
import ast


def building_utm_center(building_fp):
    building_mesh = mesh.Mesh.from_file(building_fp)
    building_mesh_a = import_stl(building_mesh)

    x_coordinates_list = []
    y_coordinates_list = []
    z_coordinates_list = []

    for triangle in building_mesh_a:
        x_coordinates_list.extend([pair[0] for pair in triangle])
        y_coordinates_list.extend([pair[1] for pair in triangle])
        z_coordinates_list.extend([pair[2] for pair in triangle])

    x = round(sum(x_coordinates_list) / len(x_coordinates_list), 3)
    y = round(sum(y_coordinates_list) / len(y_coordinates_list), 3)
    z = round(min(z_coordinates_list), 3)
    building_center = [x, y, z]
    return building_center


def triangle_norming(triangles_a, utm_center):
    triangles_a_normed = []
    for triangle in triangles_a:
        normed_triangle = []
        for point in triangle:
            normed = np.array(point) - np.array(utm_center)
            normed_point = [round(num, 3) for num in normed]
            normed_triangle.append(normed_point)
        triangles_a_normed.append(normed_triangle)
    return triangles_a_normed


'''project_folder = r'G:\Shared drives\04_Sales_and_Operations\03_Operations\Twin_Hatten\Gewobag_Pilot'
building_path = os.path.join(project_folder, 'DigitalTwin', 'STLfiles', 'target_building_positioned.stl')
utm_center = building_utm_center(building_path)

tp_path = os.path.join(project_folder, 'DigitalTwin', 'STLfiles', 'target_building_positioned2.stl')

building_mesh = mesh.Mesh.from_file(tp_path)
building_mesh_a = import_stl(building_mesh)

building_center = building_utm_center(tp_path)

import utm

a = utm.to_latlon(392457.28, 5824166.829, 33, 'U')
[392451.5, 5824171.845, 47.44]

normed_target_building = triangle_norming(building_mesh_a, building_center)
export_stl(project_folder, normed_target_building, 'Windows')
'''