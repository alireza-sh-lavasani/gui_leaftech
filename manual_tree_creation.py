import os
import stl
import numpy as np
from shapely.geometry import Point, MultiPoint, Polygon
from stl import mesh
import random
from read_json_files import read_json_files
import utm
from normalising_stl_files import building_utm_center


INPUT_FILES_FP = r'G:\Shared drives\07_Technology\07_technology\00_input_files'
# CATEGORY_DICT = os.path.join(INPUT_FILES_FP, 'category_d.json')
# CATEGORY_DICT = r'G:\Shared drives\07_Technology\07_technology\00_input_files\categoryDict\category_d.json'
TREES_FP = os.path.join(INPUT_FILES_FP, 'trees_stl')
CATEGORY_DICT = os.path.join(INPUT_FILES_FP, 'categoryDict', 'category_d.json')


class Distance:
    @classmethod
    def create_distance_list(cls, points_shape, target_building_centroid):
        cls.points_shape = points_shape
        cls.target_building_centroid = target_building_centroid

        distance_list = []
        if any(isinstance(i, list) for i in cls.points_shape[0]):
            for point_cluster in cls.points_shape:
                for point_shape in point_cluster:
                    distance_list.append(np.linalg.norm(np.array(cls.target_building_centroid) - np.array(point_shape)))
        else:
            for point_shape in cls.points_shape:
                distance_list.append(np.linalg.norm(np.array(cls.target_building_centroid) - np.array(point_shape)))
        return distance_list


def distance_max_from_class(points_shape, target_building_centroid):
    """
    This function is used to determine the maximum distance a shape of points and the target building's centroid.
    :param points_shape: Points taken into consideration (e.g. points_buildings, points_topography, points_vegetation).
    :param target_building_centroid: The UTM coordinates of the target building's centroid
    :return maximum_distance: The maximum distance between the shape of points and the centroid.
    """
    distance_list = Distance.create_distance_list(points_shape, target_building_centroid)
    maximum_distance = round(max(distance_list), 2)
    return maximum_distance


def import_stl(mesh_file):
    triangles_meshed = np.empty(len(mesh_file), dtype=object)
    for position, data in enumerate(mesh_file.data):
        data_new = data[1].tolist()
        data_new.append(data[1][0].tolist())
        data_new_a = np.array(data_new)
        triangles_meshed[position] = data_new_a
    return triangles_meshed


def scale_triangles(triangles, width_scale, height_scale):
    for i in range(len(triangles)):
        for j in range(3):
            triangles[i][j][0] = triangles[i][j][0] * width_scale
            triangles[i][j][1] = triangles[i][j][1] * width_scale
            triangles[i][j][2] = triangles[i][j][2] * height_scale
    return triangles


def triangle_array_to_stl(triangles, filepath):
    point_count = len(triangles)
    data = np.zeros(point_count, dtype=stl.mesh.Mesh.dtype)
    for i, j in enumerate(triangles):
        data["vectors"][i] = np.array([j[0], j[1], j[2]])

    tree_mesh = stl.mesh.Mesh(data)
    tree_mesh.save(filepath)


def xy_centroid_function(points):
    """
    Gives the xy centre coordinate of a set of points at the minimum z height
    :param points: points from which centre is found
    :return: point that is at the base of the centre of the tree
    """
    length = points.shape[0]
    sum_x = np.sum(points[:, 0])
    sum_y = np.sum(points[:, 1])
    low_z = min(points[:, 2])
    try:
        return sum_x / length, sum_y / length, low_z
    except ZeroDivisionError:
        print("Size of given point cloud is 0")


def midpoint_max_height_triangles(triangles):
    """
    Gives the midpoint and the maximum height from a set of triangles
    :param triangles: triangles that are analysed
    :return: the xy mid point of tree at lowest height (base) and maximum height of tree
    """
    points = []
    heights = []
    for i in range(len(triangles)):
        for j in range(3):
            points.append(triangles[i][j])
            heights.append(triangles[i][j][2])
    points = np.array(points)
    unique_points = np.unique(points, axis=0)
    mid_point = list(xy_centroid_function(unique_points))
    max_height = max(heights) - mid_point[2]
    return mid_point, max_height


def reorient_points(points, reference_point):
    """
    Reorients points so that the origin is the reference point
    :param points: points that are to be reoriented
    :param reference_point: new origin point
    :return: the newly reoriented points
    """
    print(points)
    for i in range(len(points)):
        for j in range(3):
            points[i][j][0] = points[i][j][0] - reference_point[0]
            points[i][j][1] = points[i][j][1] - reference_point[1]
            points[i][j][2] = points[i][j][2] - reference_point[2]
    return points


def resize_reorient_triangles(triangles, width_value, height_value):
    """
    Reorients and resizes a set of triangles. When width and/or height are 0, triangles are only reoriented.
    :param triangles: triangles to be altered
    :param width_value: diameter that the tree should be resized to
    :param height_value: height that the tree should be resized to
    :return: array of altered triangles
    """
    maximum_radius = 0
    centre_point, max_height = midpoint_max_height_triangles(triangles)

    if width_value != 0 and height_value != 0:
        for i in triangles:  # finds original diameter of tree
            for j in i:
                sub_maximum = np.linalg.norm(np.array(j[:2]) - np.array(centre_point[:2]))
                if sub_maximum > maximum_radius:
                    maximum_radius = sub_maximum
        maximum_diameter = maximum_radius * 2
        width_scale = width_value / maximum_diameter
        height_scale = height_value / max_height

        scale_triangles(triangles, width_scale, height_scale)

    return triangles


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


def array_centering(triangles_a, veg_center):
    triangles_a_normed = []
    for triangle in triangles_a:
        normed_triangle = []
        for point in triangle:
            normed = np.array(point) + np.array(veg_center)
            normed_point = [round(num, 3) for num in normed]
            normed_triangle.append(normed_point)
        triangles_a_normed.append(normed_triangle)
    return triangles_a_normed


def stl_to_triangle_array(filepath):
    tree_mesh = stl.mesh.Mesh.from_file(filepath)
    triangles = []
    for i in range(len(tree_mesh.vectors)):
        triangles.append(tree_mesh.vectors[i])
    return np.array(triangles)


def creating_2d_convex_hull(points):
    """
    The function takes points as XY coordinates, creates the smallest possible polygon containing all the points and
    returns an array of arrays  [X,Y].
    :param points: Coordinates of points on the surfaces that are not walls (i.e. roof, ground)
    :return: Returns the smallest possible polygon containing all the points
    """
    hull = MultiPoint(points).convex_hull
    polygon_a = []

    for x, y in hull.exterior.coords:
        polygon_a.append([x, y])

    return polygon_a


def hull_check(points):
    """
    This function is an extension to the creating_2D_convex_hull function. Here, we check if the points that we consider
    are in a single list or in a list of lists, and we create the hull according to that information.
    :param points: Points taken in consideration (e.g. target_shape, points_buildings)
    :return hulls: the smallest possible polygon containing all the points.
    """
    hulls = []
    if any(isinstance(i, list) for i in points[0]):
        for point_cluster in points:
            hulls.append(creating_2d_convex_hull(point_cluster))
    else:
        hulls = creating_2d_convex_hull(points)
    return hulls


def point_in_polygon(center_point, polygon_a):
    """
    This function takes a point and an array defining a polygon and checks if the given point is inside the polygon
    :param center_point: An array containing the UTM coordinates of the point
    :param polygon_a: The convex hull created from points located on the building's surfaces that are not walls.
    :return: Boolean expression. True if the polygon contains the point, False otherwise.
    """
    shp_point = Point(center_point)
    shp_polygon = Polygon(polygon_a)
    return shp_polygon.contains(shp_point)


def calculate_tree_height(project_folder, object_d_vegetation, tree_name):
    tree_shape = object_d_vegetation[tree_name]['shape']
    hull_target = hull_check(tree_shape)
    dsm_file_path = os.path.join(project_folder, 'GeospatialData', 'DSM')
    dtm_file_path = os.path.join(project_folder, 'GeospatialData', 'DTM')
    dtm_file = None
    dsm_file = None

    tree_shape_utm_easting = []
    tree_shape_utm_northing = []
    for i in tree_shape:
        if int(str(i[0])[:3]) % 2 == 0:
            tree_shape_utm_easting.append(int(str(i[0])[:3]))
        else:
            tree_shape_utm_easting.append(int(str(i[0])[:3]))

        if int(str(i[1])[:4]) % 2 == 0:
            tree_shape_utm_northing.append(int(str(i[1])[:4]))
        else:
            tree_shape_utm_northing.append(int(str(i[1])[:4]) - 1)
    needed_layers = [list(set(tree_shape_utm_easting)), list(set(tree_shape_utm_northing))]
    print('needed layers', needed_layers)

    coordinate_list_dsm = []
    coordinate_list_dtm = []

    point_list_dtm = []
    point_list_dsm = []

    x_unique = list(set([str(x[0])[:5] for x in hull_target]))
    y_unique = list(set([str(x[1])[:5] for x in hull_target]))
    for easting in needed_layers[0]:
        for northing in needed_layers[1]:
            file_name = str(easting) + "_" + str(northing)
            dsm_files = [file.split('.')[0] for file in os.listdir(dtm_file_path)]
            dsm_extension = list(set([file.split('.')[1] for file in os.listdir(dsm_file_path)]))
            dtm_files = [file.split('.')[0] for file in os.listdir(dsm_file_path)]
            dtm_extension = list(set([file.split('.')[1] for file in os.listdir(dtm_file_path)]))
            if file_name in dsm_files:
                dsm_file = open(os.path.join(dsm_file_path, f'{file_name}.{dsm_extension[0]}'), encoding='utf8')
            if file_name in dtm_files:
                dtm_file = open(os.path.join(dtm_file_path, f'{file_name}.{dtm_extension[0]}'), encoding='utf8')
            print('dtm file', dtm_file)
            for i in dtm_file:
                unique_coordinate = list(map(float, i.split()))
                if len(str(int(unique_coordinate[0]))) == 8:
                    unique_coordinate[0] = float(str(unique_coordinate[0])[2:])
                if str(unique_coordinate[0])[:5] in x_unique and str(unique_coordinate[1])[:5] in y_unique:
                    coordinate_list_dtm.append(unique_coordinate)
            for unique_coordinate in coordinate_list_dtm:
                if point_in_polygon(unique_coordinate, hull_target):
                    point_list_dtm.append(unique_coordinate)
            print(str(len(point_list_dtm)), " belong in the dtm file.")
            print(dsm_file)
            for i in dsm_file:
                unique_coordinate = list(map(float, i.split()))
                if len(str(int(unique_coordinate[0]))) == 8:
                    unique_coordinate[0] = float(str(unique_coordinate[0])[2:])
                if str(unique_coordinate[0])[:5] in x_unique and str(unique_coordinate[1])[:5] in y_unique:
                    coordinate_list_dsm.append(unique_coordinate)
            for unique_coordinate in coordinate_list_dsm:
                if point_in_polygon(unique_coordinate, hull_target):
                    point_list_dsm.append(unique_coordinate)
            print(str(len(point_list_dsm)), " belong in the dsm file.")

            max_point_dsm = max([point[2] for point in point_list_dsm])
            min_point_dtm = min([point[2] for point in point_list_dtm])
            tree_height = round(max_point_dsm - min_point_dtm, 2)
            return max_point_dsm, min_point_dtm, tree_height


def get_scales(triangle_array, diameter, height):
    centre_point, max_height = midpoint_max_height_triangles(triangle_array)
    maximum_radius = 0
    width_scale = None
    height_scale = None
    if diameter != 0 and height != 0:
        for point in triangle_array:  # finds original diameter of tree
            for coordinate in point:
                sub_maximum = np.linalg.norm(np.array(coordinate[:2]) - np.array(centre_point[:2]))

                if sub_maximum > maximum_radius:
                    maximum_radius = sub_maximum
        maximum_diameter = maximum_radius * 2
        width_scale = diameter / maximum_diameter
        height_scale = height / max_height

    return width_scale, height_scale


# 1 create object_d_vegetation

def random_tree_model_placement(building_center_point, project_folder, tree_name,
                                object_d_vegetation):
    tree_end_file_path = os.path.join(project_folder, 'DigitalTwin', 'STLfiles', 'remodeled_trees')
    max_point_dsm, min_point_dtm, height = calculate_tree_height(project_folder, object_d_vegetation, tree_name)
    diameter = distance_max_from_class(object_d_vegetation[tree_name]['shape'],
                                       object_d_vegetation[tree_name]['centroid']) * 0.8 * 2

    random_tree = random.choice(os.listdir(TREES_FP))
    triangles_tb_mesh = mesh.Mesh.from_file(os.path.join(TREES_FP, random_tree))
    model_tree_a = import_stl(triangles_tb_mesh)

    real_tree_center_point = list(object_d_vegetation[tree_name]['centroid'])
    real_tree_center_point.append(min_point_dtm)

    width_scale_value, height_scale_value = get_scales(model_tree_a, diameter, height)
    scaled_triangles = scale_triangles(model_tree_a, width_scale_value, height_scale_value)

    centered_triangle_a = array_centering(scaled_triangles, real_tree_center_point)
    normed_triangle = triangle_norming(centered_triangle_a, building_center_point)

    triangle_array_to_stl(normed_triangle, os.path.join(tree_end_file_path, tree_name + '_remodeled.stl'))
    print(f'{tree_name} done')


def selected_tree_model_placement(building_center_point, project_folder, tree_name,
                                  object_d_vegetation, model_tree):
    tree_end_file_path = os.path.join(project_folder, 'DigitalTwin', 'STLfiles', 'remodeled_trees')
    max_point_dsm, min_point_dtm, height = calculate_tree_height(project_folder, object_d_vegetation, tree_name)
    diameter = distance_max_from_class(object_d_vegetation[tree_name]['shape'],
                                       object_d_vegetation[tree_name]['centroid']) * 0.8 * 2

    selected_tree = os.path.join(INPUT_FILES_FP, 'tree_stl', f'{model_tree}.stl')
    triangles_tb_mesh = mesh.Mesh.from_file(selected_tree)
    model_tree_a = import_stl(triangles_tb_mesh)

    real_tree_center_point = list(object_d_vegetation[tree_name]['centroid'])
    real_tree_center_point.append(min_point_dtm)

    width_scale_value, height_scale_value = get_scales(model_tree_a, diameter, height)
    scaled_triangles = scale_triangles(model_tree_a, width_scale_value, height_scale_value)

    centered_triangle_a = array_centering(scaled_triangles, real_tree_center_point)
    normed_triangle = triangle_norming(centered_triangle_a, building_center_point)

    triangle_array_to_stl(normed_triangle, os.path.join(tree_end_file_path, tree_name + '_remodeled.stl'))
    print(f'{tree_name} done')


def centroid_function(array):
    """
    Given a coordinate array [[x1, y1],...,[xn, yn]], this function finds the centroid point of the x and y coordinates.
    :param array: The array we want to its center point.
    :return round(sum_x / length, 2), round(sum_y / length, 2): The centroid point of the coordinate array.
    """
    length = array.shape[0]
    try:
        sum_x = np.sum(array[:, 0])
        sum_y = np.sum(array[:, 1])
        center_x = round(sum_x / length, 2)
        center_y = round(sum_y / length, 2)
        return center_x, center_y
    except ZeroDivisionError:
        print('empty array provided.')


def polygon_from_kml(kml_file_path, category_d):
    """
    This function parses through a given KML file and creates polygons containing relevant data points. Additionally,
    it converts the given lat long data into UTM coordinates.
    :param kml_file_path: Folder where the KML file for the project is stored.
    :param category_d: Dictionary containing data necessary for parsing the KML files.
    :return object_d: A list of polygons in a dictionary for a given category.
    """
    object_d = {"objects": []}
    kml_data = open(kml_file_path, "r")
    polygon_found = False
    layer_found = False
    single_object_start = False
    object_type = 'meh'
    shape_a = None
    name = None
    centroid = None

    for line in kml_data:
        line = line.strip("\n")
        line = line.strip("\t")
        line = line.strip(" ")

        if category_d['singleObject_end'] in line:
            single_object_start = False

        if single_object_start:
            if category_d['ID_start'] in line:
                line_6 = line[6:].split("<")
                name = line_6[0]
                # print(name)

        if category_d['singleObject_start'] in line:
            single_object_start = True

        if category_d['category_end'] in line:
            layer_found = False

        if layer_found and single_object_start is False:
            if category_d['ID_start'] in line:
                line_b = line.split(">")
                line_c = line_b[1].split("</")
                object_type = line_c[0]
                # print(type)
        if category_d['category_start'] in line:
            layer_found = True
            # print(line)

        if category_d["polygon_end"] in line:
            polygon_found = False
            polygon_d = {"shape": shape_a, "TYPE": object_type, "ID": name, "centroid": centroid}
            object_d["objects"].append(polygon_d)
        if polygon_found:
            line_a = line.split(",")
            line_a = line_a[:-1]
            string_array = np.array(line_a)
            float_array = string_array.astype(np.float)
            utm_a = utm.from_latlon(float_array[1], float_array[0])
            shape_a.append([round(utm_a[0], 2), round(utm_a[1], 2)])
            points_array = np.array(shape_a)
            centroid = centroid_function(points_array)

        if category_d["polygon_start"] in line:
            polygon_found = True
            shape_a = []

    return object_d


def get_object_d_vegetation(project_file_path):
    kml_folder = os.path.join(project_file_path, 'GeospatialData', 'KML')
    kml_file_name = os.listdir(kml_folder)[0]

    kml_fp = os.path.join(kml_folder, kml_file_name)
    category_d = read_json_files(CATEGORY_DICT)
    json_dict = polygon_from_kml(kml_fp, category_d)

    object_d_vegetation = {}
    for i in json_dict['objects']:
        if i['TYPE'] == 'Vegetation':
            object_d_vegetation[i['ID']] = i
        if i['TYPE'] == 'TargetBuilding':
            object_d_vegetation[i['ID']] = i
    return object_d_vegetation



"""project_folder = r'G:\Shared drives\04_Sales_and_Operations\03_Operations\Twin_Hatten\Gewobag_Pilot'
stl_folder = os.path.join(project_folder, 'DigitalTwin', 'STLfiles')
building_path = os.path.join(stl_folder, 'target_building_raytracing.stl')

object_d_veg = get_object_d_vegetation(project_folder)

url = 'https://api.apps.leaftech.eu/api/'
username = 'ratomir.dimikj@leaftech.eu'
password = '89Bf%772C:369=z@2%%X'
project_id = 29
credentials_d = {'username': username, 'password': password}
token_fp = r'G:\Shared drives\07_Technology\07_technology\00_input_files\TokenCredentials\api_token_otc.json'
from obtain_token import obtain_token
token = obtain_token(token_fp, url)

tree_names = [tree for tree in list(object_d_veg.keys()) if 'Tree' in tree]

building_center_point = building_utm_center(building_path)

for tree_name in tree_names:
    if tree_name+'_remodeled.stl' not in os.listdir(os.path.join(stl_folder, 'remodeled_trees')):
        print(tree_name)
        random_tree_model_placement(building_center_point, project_folder, tree_name,
                                    object_d_veg)
"""