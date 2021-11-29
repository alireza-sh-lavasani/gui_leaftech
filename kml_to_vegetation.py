from polygon_from_kml import polygon_from_kml
from get_relevant_data import get_relevant_data
import os
import json
import numpy as np
import utm


def distance_max(vegetation_points_list, center_point_utm_a):
    maximum_distance = 0
    if any(isinstance(i, list) for i in vegetation_points_list[0]):
        for i in vegetation_points_list:
            for j in i:
                sub_maximum = np.linalg.norm(j - center_point_utm_a)
                if sub_maximum > maximum_distance:
                    maximum_distance = sub_maximum
    else:
        for i in vegetation_points_list:
            sub_maximum = np.linalg.norm(i - center_point_utm_a)
            if sub_maximum > maximum_distance:
                maximum_distance = sub_maximum
    return maximum_distance


def check_distance(point_a, point_b, max_distance):
    return max_distance > np.linalg.norm(point_b - point_a)


def create_relevant_point_cloud(points, center_point_utm_a, max_distance):
    point_cloud_a = thin_out_points(points, center_point_utm_a, max_distance)

    point_cloud_a = np.array(point_cloud_a)

    '''
    highest_point = [0, 0, 0]
    for i in point_cloud_a:
        if i[2] > highest_point[2]:
            highest_point = i
    highest_point = np.array(highest_point[0:2])

    point_cloud_a = thin_out_points(points, highest_point, max_distance)
    '''

    return point_cloud_a


def thin_out_points(points, center_point_utm_a, max_distance):
    point_cloud_a = []

    if type(points).__module__ == np.__name__:
        for i in points:
            if check_distance(center_point_utm_a, i[0:2], max_distance):
                point_cloud_a.append(i)

    else:
        if not isinstance(points, list):
            points = [points]

        for i in points:
            with open(i, encoding='utf8') as dsm_data_txt:
                for line in dsm_data_txt:
                    dsm_xyz = []
                    for j in line.split():
                        dsm_xyz.append(float(j))
                    if check_distance(center_point_utm_a, dsm_xyz[0:2], max_distance):
                        point_cloud_a.append(dsm_xyz)

    return point_cloud_a


def scatter_plot(points):
    xp = [row[0] for row in points]
    yp = [row[1] for row in points]
    zp = [row[2] for row in points]

    fig = plt.figure()
    ax = Axes3D(fig)
    ax.scatter(xp, yp, zp, s=1, c='Green')
    plt.show()

    return


def create_tree_dict(object_d_vegetation):
    """
    {
    'quadrant': 'nnn-eeee',
    'latitude': float,
    'longitude': float,
    'utmX': float,
    'utmY': float,
    'points' [basically the point cloud obtained above],
    'object_name': '..'
    }
    """
    object_my_tree = object_d_vegetation.get('objects')[0]
    first_digits_a = str(object_my_tree.get('shape')[0][0])[:3]
    first_digits_b = str(object_my_tree.get('shape')[0][1])[:4]
    utmX = float(object_my_tree.get('centroid')[0])
    utmY = float(object_my_tree.get('centroid')[1])
    lat, long = utm.to_latlon(utmX, utmY, 33, 'U')
    tree_dict = {
        'quadrant': first_digits_a + '-' + first_digits_b,
        'latitude': lat,
        'longitude': long,
        'utmX': utmX,
        'utmY': utmY,
    #    'points': vegetation_point_cloud,
        'object_name': object_my_tree.get('ID')
    }
    return tree_dict


def point_cloud_to_xyz(point_cloud, file_path):
    file = open(file_path, 'w')
    for i in point_cloud:
        for j in i:
            file.write(str(j) + ' ')
        file.write('\n')
    file.close()


def kml_to_vegetation(category_d_fp, project_folder, file_name):
    with open(os.path.join(category_d_fp)) as f:
        category_d = json.load(f)
    vegetation_kml_fp = os.path.join(project_folder, 'GeospatialData', 'KML', file_name)
    vegetation_json_dict = polygon_from_kml(vegetation_kml_fp, category_d)
    centroid_point_target_bldg, points_buildings, points_vegetation, points_topography, object_d_vegetation, \
        target_shape = get_relevant_data(vegetation_json_dict)
    return points_vegetation, object_d_vegetation


def kml_to_building(project_folder, tree_name):
    category_d_fp = '/Volumes/GoogleDrive/Shared drives/Julia/Julia_onboarding/data/category_d.json'
    with open(os.path.join(category_d_fp)) as f:
        category_d = json.load(f)
    kml_fp = project_folder + 'GeospatialData/KML/' + tree_name + '.kml'
    json_dict = polygon_from_kml(kml_fp, category_d)
    centroid_point_target_bldg, points_buildings, points_vegetation, points_topography, object_d_vegetation, \
        target_shape = get_relevant_data(json_dict)
    return centroid_point_target_bldg, points_buildings, target_shape


