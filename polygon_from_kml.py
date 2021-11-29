import numpy as np
import utm


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
        if category_d['category_start'] in line:
            layer_found = True
            # print(line)

        if category_d["polygon_end"] in line:
            polygon_found = False
            polygon_d = {"shape": shape_a, "TYPE": object_type, "ID": name, "centroid": centroid}
            object_d["objects"].append(polygon_d)
        if polygon_found:
            #print(line)
            line_a = line.split(",")
            line_a = line_a[:-1]
            string_array = np.array(line_a)
            float_array = string_array.astype(np.float)
            # print('LATITUDE LONGITUDE', float_array[1], float_array[0])
            utm_a = utm.from_latlon(float_array[1], float_array[0])
            # print('UTM', utm_a)
            shape_a.append([round(utm_a[0], 2), round(utm_a[1], 2)])
            points_array = np.array(shape_a)
            centroid = centroid_function(points_array)

        if category_d["polygon_start"] in line:
            polygon_found = True
            shape_a = []

    return object_d


def centroid_function(array):
    """
    Given a coordinate array [[x1, y1],...,[xn, yn]], this function finds the centroid point of the x and y coordinates.
    :param array: The array we want to its center point.
    :return round(sum_x / length, 2), round(sum_y / length, 2): The centroid point of the coordinate array.
    """
    length = array.shape[0]
    sum_x = np.sum(array[:, 0])
    sum_y = np.sum(array[:, 1])
    return round(sum_x / length, 2), round(sum_y / length, 2)