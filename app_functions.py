import os
import shutil
from json import load, dumps
import open3d as o3d
from requests import request
import numpy as np
import requests
from subprocess import call
import time
import gzip
import zipfile
import json
import utm
import alphashape
import ast
from stl import mesh
from shapely.geometry import Point, MultiPoint, Polygon
from scipy.spatial import Delaunay
from manual_tree_creation import random_tree_model_placement, selected_tree_model_placement
from unique_list_coordinates import unique_list_coordinates

PATH = os.getcwd()
print(PATH)
INPUT_FILES_FP = os.path.join(PATH, 'data')
CATEGORY_DICT = os.path.join(INPUT_FILES_FP, 'category_d.json')


def read_json_files(file_path):
    json_filename = str(file_path)
    with open(json_filename, 'r') as fp:
        dict_d = json.load(fp)
    return dict_d


def post_request(server_address, access_token, table_path, payload_json, printing=False):
    """
    A function that is used to send data to the server to create an item in the database. The POST endpoints always
    return the specified endpoint item. Parameters are send in the body of the request which is in JSON format.

    :param server_address: hostname of the environment where we post the data. We have 3 different environments to
    which the app is being deployed.
    :param access_token: contains the security credentials for a login session and identifies the user, the user's
    groups, the user's privileges, and, in some cases, a particular application. Access tokens only have a limited
    lifetime.
    :param table_path: The specific sub-location of a given table on the server.
    :param payload_json: The Payload of an API Module is the body of your request and response message. It contains
    the data that you send to the server when you make an API request. You can send and receive Payload in different
    formats, in this instance it is 
    :param printing: Boolean operator that allows us to choose whether we want to print the response of the request
    or not.
    :return response.json(): The json dictionary of the created item.
    """
    headers = {
        'Authorization': 'Bearer %s' % access_token,
        'Content-Type': 'application/json'
    }
    response = request("POST", os.path.join(server_address, table_path).replace('\\', "/"), headers=headers,
                       data=payload_json)
    if printing:
        if response.status_code == 201:
            print("Response status code:",
                  response.status_code, "successful post.")
        else:
            print("Response status code:",
                  response.status_code, "Something is wrong,")
        # print(response.text.encode('utf8'))
    return response.json()


def patch_request(server_address, access_token, table_path, item_id, payload_json, printing=False):
    """
    This function allows any item attribute to be send as body parameter in the request, which will modify the
    specified attribute in the database. The response will be the modified item.

    :param server_address: hostname of the environment where we post the data. We have 3 different environments to
    which the app is being deployed.
    :param access_token: contains the security credentials for a login session and identifies the user, the user's
    groups, the user's privileges, and, in some cases, a particular application. Access tokens only have a limited
    lifetime.
    :param table_path: The specific sub-location of a given table on the server.
    :param item_id: The ID of the item that we want to delete.
    :param payload_json: The Payload of an API Module is the body of your request and response message. It contains
    the data that you send to the server when you make an API request. You can send and receive Payload in different
    formats, in this instance it is 
    :param printing: Boolean operator that allows us to choose whether we want to print the response of the request
    or not.
    :return response.json(): The json dictionary of the modified item.
    """
    headers = {
        'Authorization': 'Bearer %s' % access_token,
        'Content-Type': 'application/json'
    }
    response = request("PATCH", os.path.join(server_address, table_path, str(item_id)).replace("\\", '/'),
                       headers=headers, data=payload_json)
    if printing:
        print(response.text.encode('utf8'))
    return response.json()


def obtain_token(token_credentials, server_address):
    """
    This function is used to obtain the security access token, given some oauth credentials and a server address that
    we want to have access to.
    :param token_credentials: file_path where the credentials are stored
    :param server_address: hostname of the environment where we post the data. We have 3 different environments to
    which the app is being deployed.
    :return: access_token: contains the security credentials for a login session and identifies the user, the user's
    groups, the user's privileges, and, in some cases, a particular application. Access tokens only have a limited
    lifetime.
    """
    payload = {
        "grant_type": 'password',
        "client_id": 'vue-frontend',
        "username": token_credentials['username'],
        "password": token_credentials['password']
    }
    response = request("POST", os.path.join(server_address, 'oauth').replace("\\", "/"),
                       headers={
                           "Content-Type": "application/x-www-form-urlencoded"},
                       data=payload)
    response_dict = response.json()
    try:
        if response_dict['title']:
            return None
    except KeyError:
        access_token = response_dict['access_token']
        return access_token


def get_request(server_address, access_token, table_path, printing=False, **kwargs):
    """
    :param server_address: hostname of the environment where we post the data. We have 3 different environments to
    which the app is being deployed.
    :param access_token: contains the security credentials for a login session and identifies the user, the user's
    groups, the user's privileges, and, in some cases, a particular application. Access tokens only have a limited
    lifetime.
    :param table_path: The specific sub-location of a given table on the server.
    :param printing: Boolean operator that allows us to choose whether we want to print the response of the request
    or not.
    :param kwargs: dictionary - whose keys become separate keyword arguments and the values become values of these
    arguments. The additional query parameters are used e.g. customerId, projectId, clusterId, limit etc.
    :return response_json: The JSON dictionary that contains the response for the GET request.
    """
    payload = {}
    headers = {'Authorization': 'Bearer %s' % access_token}
    url_basic = os.path.join(server_address, table_path).replace("\\", "/")
    url_final = os.path.join(server_address, table_path).replace("\\", "/")

    for kw_key, kw_value in kwargs.items():
        if url_final == url_basic:
            url_final = os.path.join(
                url_basic + "?{}=".format(kw_key) + str(kw_value)).replace("\\", "/")
        else:
            url_final = os.path.join(
                url_final + "&{}=".format(kw_key) + str(kw_value)).replace("\\", "/")
    response = request("GET", url_final, headers=headers, data=payload)
    if printing:
        print('url final', url_final)
        print(response.text.encode('utf8'))
    response_json = response.json()
    return response_json


def setup_project(project_name):
    folder_name = project_name.replace(" ", "_")
    source_path = os.path.join(os.getcwd(), 'data', '00_StandardFolder')

    # shared_folders_name = os.getcwd().split('07_Technology')[0]
    # destination_path = os.path.join(shared_folders_name, '04_Sales_and_Operations', '03_Operations', 'Twin_Hatten',
    #                                 folder_name)

    """
      Create projects folders in the root of the project 
      and create a folder named project_name inside
    """
    destination_path = os.path.join(os.getcwd(), 'projects', folder_name)

    if not os.path.isdir(destination_path):
        shutil.copytree(source_path, destination_path)

    config_dict = return_config_dict(destination_path)
    config_dict["ProjectName"] = project_name
    config_dict["FolderName"] = folder_name
    write_config_dict(config_dict, destination_path)
    return destination_path


def project_setup(config_file, customer_id, server_address, access_token):
    get_existing_projects = get_request(
        server_address, access_token, 'projects', limit=10000)['list']
    existing_projects_d = {project['name']: project['id']
                           for project in get_existing_projects}
    if config_file['ProjectName'] in existing_projects_d:
        project_id = existing_projects_d[config_file['ProjectName']]
        return project_id
    else:
        if config_file['WeatherAPI'] == 'off':
            processing = 'false'
        else:
            processing = 'true'
        payload_project_data = dumps({
            'name': config_file['ProjectName'],
            'street': config_file['street'],
            'postCode': config_file['postCode'],
            'city': config_file['city'],
            'country': config_file['Country'],
            'processing': processing,
            'customerId': customer_id,
            'referenceLongitude': 15,
            'language': config_file['Language']
        })
        project = post_request(server_address, access_token,
                               "projects", payload_project_data)
        project_id = project['id']

        return project_id


def customer_setup(customer_name, customer_language, server_address, access_token):
    print('server address', server_address)
    get_existing_customers = get_request(
        server_address, access_token, "customer", limit=10000)['list']
    existing_customer_d = {customer['name']: customer['id']
                           for customer in get_existing_customers}
    if customer_name in existing_customer_d:
        customer_id = existing_customer_d[customer_name]
        return customer_id

    else:
        if customer_language == 'English':
            customer_language = 'en'
        else:
            customer_language = 'de'
        customer_payload = {
            "language": customer_language,
            "name": customer_name
        }
        customer_payload_json = dumps(customer_payload)
        post_customer = post_request(
            server_address, access_token, 'customer', customer_payload_json, printing=True)
        customer_id = post_customer['id']
        return customer_id


def return_config_dict(destination_path):
    config_path = os.path.join(destination_path, 'DigitalTwin', 'config')
    with open(config_path, 'r') as fp:
        config_dict = load(fp)
    return config_dict


def return_building_dict(folder_name):
    config_path = os.path.join(
        'projects', folder_name, 'building_config.txt')
    building_dict = {"folderpath": "",
                     "dxffilename": "",
                     "clustersortingfilename": "",
                     "clusterinformationfilename": "",
                     "buildingname": "",
                     "floorname": "",
                     "floorheight": "",
                     "separator": "",
                     "layer_section_keys": "",
                     "layer_surface_keys": "",
                     "dxf_data_types": "",
                     "multiplepersection": ""}
    with open(config_path, 'r') as file:
        all_lines = file.readlines()
        for line in all_lines:
            if line[0] == '#':
                for i in range(len(line)):
                    if line[i] == ';':
                        value_start = i
                key_name = line[1:value_start]
                value_name = line[value_start + 1:-1]
                print(key_name)
                print(value_name)
                building_dict[key_name] = value_name

    return building_dict


def write_config_dict(config_dict, destination_path):
    try:
        config_path = os.path.join(destination_path, 'DigitalTwin', 'config')
    except:
        config_path = os.path.join(
            destination_path, 'DigitalTwin', 'config.txt')
    with open(config_path, 'w') as file:
        file.write(dumps(config_dict))


def write_building_dict(config_dict, folder_name, config_name):
    config_path = os.path.join('project_database', folder_name, config_name)
    with open(config_path, 'w') as file:
        print(config_dict)
        for key in config_dict:
            file.write('#')
            file.write(key)
            file.write(';')
            file.write(config_dict[key])
            file.write("\n")
            file.write("\n")


def manual_stl_download(destination_path, reference_point, model_tree, object_d_veg):
    stl_folder = os.path.join(destination_path, 'DigitalTwin', 'STLfiles')

    tree_names = [tree for tree in list(object_d_veg.keys()) if 'tree' in tree]

    for tree_name in tree_names:
        if tree_name + '_remodeled.stl' not in os.listdir(os.path.join(stl_folder, 'remodeled_trees')):
            selected_tree_model_placement(reference_point, destination_path, tree_name,
                                          object_d_veg, model_tree)
    tree_mesh_list = []
    for stl_file in os.listdir(os.path.join(stl_folder, 'remodeled_trees')):
        if 'tree' in stl_file:
            tree_mesh = mesh.Mesh.from_file(os.path.join(
                stl_folder, 'remodeled_trees', stl_file))
            tree_mesh_a = import_stl(tree_mesh)
            tree_mesh_list.append(tree_mesh_a)

    all_trees = np.concatenate(tree_mesh_list)
    export_stl(destination_path, all_trees, 'Vegetation')


# add CAD model check
def get_menu_checklist(folder_name):
    project_config = check_project_config(folder_name)
    kml_setup = check_kml_setup(folder_name)
    geodata_found = get_geodata_checklist(folder_name)
    terrain_added = check_terrain_added(folder_name)
    buildings_added = check_buildings_added(folder_name)
    vegetation_added = check_vegetation_added(folder_name)
    # surfaces_added = check_surfaces_added(folder_name)
    checklist = [project_config,
                 kml_setup,
                 geodata_found,
                 terrain_added,
                 buildings_added,
                 vegetation_added]
    return checklist


def get_complete_menu_checklist(checklist):
    return all(checklist)


def check_project_config(folder_name):
    empty_config_dict = {"ProjectName": "",
                         "ProjectID": "",
                         "FolderName": "",
                         "CustomerName": "",
                         "PartnerName": "",
                         "Country": "",
                         "County": "",
                         "services": [""],
                         "WeatherAPI": "",
                         "Language": "",
                         "Location": [0, 0, 0],
                         "street": "",
                         "postCode": 0,
                         "city": ""}

    current_config_dict = return_config_dict(folder_name)

    complete = True
    for field in empty_config_dict:
        if empty_config_dict[field] == current_config_dict[field]:
            complete = False

    return complete


def check_kml_setup(folder_name):
    kml_file_path = os.listdir(os.path.join(
        'projects', folder_name, 'GeospatialData', 'KML'))
    complete = True
    if len(kml_file_path) == 0:
        complete = False
    return complete


def get_geodata_checklist(folder_name):
    folders = ['DSM', 'DTM', 'GML']
    checklist = [0 if len(os.listdir(os.path.join(folder_name, 'GeospatialData', folder))) == 0 else 1 for folder in
                 folders]
    return all(checklist) == 1


def check_terrain_added(folder_name):
    file_path = os.path.join(
        'projects', folder_name, 'DigitalTwin', 'STLfiles', 'terrain.stl')
    complete = False
    if os.path.exists(file_path):
        complete = True
    return complete


def check_buildings_added(folder_name):
    file_path = os.path.join(
        'projects', folder_name, 'DigitalTwin', 'STLfiles', 'all_buildings.stl')
    complete = False
    if os.path.exists(file_path):
        complete = True
    return complete


def check_vegetation_added(folder_name):
    file_path = os.path.join(
        'projects', folder_name, 'DigitalTwin', 'STLfiles', 'vegetation.stl')
    print('fp', file_path)
    other_file_path = os.path.join(
        'projects', folder_name, 'DigitalTwin', 'STLfiles', 'evergreen_01.stl')
    another_file_path = os.path.join(
        'projects', folder_name, 'DigitalTwin', 'STLfiles', 'deciduous_01.stl')
    complete = False
    if os.path.exists(file_path) or os.path.exists(other_file_path) or os.path.exists(another_file_path):
        complete = True
    return complete


def check_surfaces_added(folder_name, server_address, access_token, project_id):
    target_surfaces_d = os.path.join(folder_name)
    # surfaces_in_folder =


def select_geo_template(folder_name):
    geo_info_path = os.path.join('static/geodata_information.txt')
    with open(geo_info_path, 'r') as fp:
        geo_info_dict = load(fp)
    config_dict = return_config_dict(folder_name)
    county = config_dict["County"]
    checklist = get_geodata_checklist(folder_name)
    geo_info = 0
    if county == "Berlin" or county == "NRW" or county == "Hamburg" or county == "Sachsen" or \
            county == "Brandenburg":
        geo_template = 0
    else:
        geo_template = 1
        geo_info = geo_info_dict[county]

    return county, geo_template, geo_info, checklist


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
            polygon_d = {"shape": shape_a, "TYPE": object_type,
                         "ID": name, "centroid": centroid}
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


def get_relevant_data(kml_file_path, category_d):
    """
    This function takes a previously constructed json dictionary (in the polygon_from_KML function) that contains data
    from the KML file about the four layers of information (Target buildings, surrounding buildings, vegetation,
    terrain). From this dictionary, specific information is extracted that is necessary for the further setup of the
    project.
    :param kml_file_path: Folder where the KML file for the project is stored.
    :param category_d: Dictionary containing data necessary for parsing the KML files.
    :return centroid_point_target_bldg, points_buildings, points_vegetation, points_topography, object_d_vegetation,
    target_shape: There are multiple returns from this function: the centroid point of the target building,
    the points from the buildings, vegetation and topography, the vegetation object dictionary and the target building
    shape.
    """
    json_dict = polygon_from_kml(kml_file_path, category_d)

    target_building_center = []
    target_area_center = []
    points_buildings = []
    points_vegetation = []
    points_topography = []
    centroid_point_target_bldg = []
    target_building_shape = []
    target_area_shape = []
    object_d_vegetation = {'objects': []}
    for i in json_dict['objects']:
        if i['TYPE'] == 'SurroundingBuildings':
            points_buildings.append(i['shape'])
        if i['TYPE'] == 'TargetBuilding':
            target_building_center.append(i['centroid'])
            points_buildings.append(i['shape'])
            centroid_point_target_bldg = np.array(target_building_center[0])
            target_building_shape.append(i['shape'])
        if i['TYPE'] == 'TargetArea':
            target_area_center.append(i['centroid'])
            target_area_center = np.array(target_area_center[0])
            target_area_shape.append(i['shape'])
        if i['TYPE'] == 'Vegetation':
            object_d_vegetation['objects'].append(i)
            points_vegetation.append(i['shape'])
        if i['TYPE'] == 'Topography' or i['TYPE'] == 'Terrain':
            points_topography = i['shape']
        # print('points topography', points_topography)
    return centroid_point_target_bldg, points_buildings, points_vegetation, points_topography, object_d_vegetation, \
        target_building_shape, target_area_shape, target_area_center


# need to change to download data for everything - right now, just trees
def nrw_download(unique_list_layers, geo_spatial_list, data_type):
    data_list = unique_list_layers[data_type]
    for x in data_list[0]:
        for y in data_list[1]:
            zip_file_addon = str(x) + "_" + str(y)
            download_url = geo_spatial_list[0] + \
                zip_file_addon + geo_spatial_list[1]
            url_string_split = download_url.split('/')[-1].split('.')[0]
            files_list = [file_name.split(
                '.')[0] for file_name in os.listdir(geo_spatial_list[2])]
            extension = '.' + download_url.rsplit('.', 1)[1]
            if url_string_split not in files_list:
                r = requests.get(download_url)
                print('url:', download_url, 'status code:', r.status_code)
                if r.status_code == 200:
                    file_name = os.path.join(
                        geo_spatial_list[2], zip_file_addon + extension)
                    print(data_type, file_name)
                    with open(file_name, 'wb') as f:
                        f.write(r.content)
                    if data_type == 'DSM' and zip_file_addon + extension in os.listdir(geo_spatial_list[2]):
                        cmdline = r'laszip.exe -i "{}" -otxt -oparse xyz'.format(
                            os.path.join(PATH, file_name).replace("//", "\\"))
                        print(cmdline)
                        call("start cmd /K " + cmdline,
                             cwd=INPUT_FILES_FP, shell=True)
                        print('waiting for the .laz file to be converted to .txt')
                        time.sleep(300)
                        os.remove(os.path.join(PATH, file_name))
                    elif data_type == 'DTM' and extension == '.gz' and \
                            zip_file_addon + extension in os.listdir(geo_spatial_list[2]):
                        with gzip.open(os.path.join(geo_spatial_list[2], zip_file_addon + extension),
                                       'rb') as f_in:
                            with open(os.path.join(geo_spatial_list[2], zip_file_addon + '.txt'),
                                      'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(os.path.join(PATH, file_name))
                    elif data_type == 'GML':
                        filename = os.path.join(
                            geo_spatial_list[2], zip_file_addon + extension)
                        print('filename', filename)
                        with open(filename, 'wb') as f:
                            f.write(r.content)


def berlin_download(unique_list_layers, geo_spatial_list, data_type):
    appendix = '.zip'
    data_list = unique_list_layers[data_type]
    for x in data_list[0]:
        for y in data_list[1]:
            zip_file_addon = str(x) + "_" + str(y)
            name = zip_file_addon
            download_url = geo_spatial_list[0] + zip_file_addon + appendix
            url_string_split = download_url.split('/')[-1].split('.')[0]
            files_list = [file_name.split(
                '.')[0] for file_name in os.listdir(geo_spatial_list[1])]
            if url_string_split not in files_list:
                r = requests.get(download_url)
                print('url:', download_url, 'status code:', r.status_code)
                filename = os.path.join(geo_spatial_list[1], name + '.zip')

                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    with zipfile.ZipFile(filename, 'r') as zip_ref:
                        zip_ref.extractall(geo_spatial_list[1])
                    os.remove(filename)


def hamburg_download(unique_list_layers, geo_spatial_base_fp, geo_spatial_project_fp):
    for layer in unique_list_layers:
        for key in layer:
            print(key)
            for x in layer[key][0]:
                for y in layer[key][1]:
                    zip_file_addon = str(x) + "_" + str(y)
                    for i in os.listdir(geo_spatial_base_fp):
                        if key == 'GML':
                            if i[5:13] == zip_file_addon:
                                print(zip_file_addon)
                                shutil.copy2(os.path.join(
                                    geo_spatial_base_fp, i), geo_spatial_project_fp)
                        else:
                            if i[7:15] == zip_file_addon:
                                print(zip_file_addon)
                                shutil.copy2(os.path.join(
                                    geo_spatial_base_fp, i), geo_spatial_project_fp)


def geo_data_download(project_folder, county, unique_list_layers):
    gml_folder = os.path.join(project_folder, 'GeospatialData', 'GML')
    dtm_folder = os.path.join(project_folder, 'GeospatialData', 'DTM')
    dsm_folder = os.path.join(project_folder, 'GeospatialData', 'DSM')
    print('UNIQUE LIST LAYERS', unique_list_layers)
    if county == 'NRW':
        url_base = r"https://www.opengeodata.nrw.de/produkte/geobasis/"
        gml_url_base = os.path.join(url_base, "3dg/lod2_gml/lod2_gml/LoD2_32_")
        gml_appendix = "_1_NW.gml"
        gml_list = [gml_url_base, gml_appendix, gml_folder]
        nrw_download(unique_list_layers, gml_list, 'GML')

        dsm_url_base = os.path.join(url_base, "hm/3dm_l_las/3dm_l_las/3dm_32_")
        dsm_appendix = "_1_nw.laz"
        dsm_list = [dsm_url_base, dsm_appendix, dsm_folder]
        nrw_download(unique_list_layers, dsm_list, 'DSM')

        dtm_url_base = os.path.join(url_base, "hm/dgm1_xyz/dgm1_xyz/dgm1_32_")
        dtm_appendix = "_1_nw.xyz.gz"
        dtm_list = [dtm_url_base, dtm_appendix, dtm_folder]
        nrw_download(unique_list_layers, dtm_list, 'DTM')

    elif county == 'Berlin':
        url_base = "http://fbinter.stadt-berlin.de/fb/atom/"
        dsm_url_base = url_base + "bDOM1/"
        dtm_url_base = url_base + "DGM1/"
        gml_url_base = url_base + "LOD2/LoD2_"

        gml_list = [gml_url_base, gml_folder]
        dsm_list = [dsm_url_base, dsm_folder]
        dtm_list = [dtm_url_base, dtm_folder]

        berlin_download(unique_list_layers, gml_list, 'GML')
        berlin_download(unique_list_layers, dsm_list, 'DSM')
        berlin_download(unique_list_layers, dtm_list, 'DTM')

    elif county == 'Hamburg':
        gml_base = r"G:\Shared drives\CityGML-DataBase\Germany\Hamburg"
        dsm_base = r"G:\Shared drives\CityGML-DataBase\Germany\Hamburg_surface"
        dtm_base = r"G:\Shared drives\CityGML-DataBase\Germany\Hamburg_surface"

        gml_folder = os.path.join(project_folder, 'GeospatialData', 'GML')
        dtm_folder = os.path.join(project_folder, 'GeospatialData', 'DTM')
        dsm_folder = os.path.join(project_folder, 'GeospatialData', 'DSM')

        hamburg_download(unique_list_layers, gml_base, gml_folder)
        hamburg_download(unique_list_layers, dsm_base, dsm_folder)
        hamburg_download(unique_list_layers, dtm_base, dtm_folder)


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


def automatic_stl_download(folder_path, reference_point):
    # folder_path = os.path.join('projects', folder_name)
    stl_folder = os.path.join(folder_path, 'DigitalTwin', 'STLfiles')

    object_d_veg = get_object_d_vegetation(folder_path)

    tree_names = [tree for tree in list(object_d_veg.keys()) if 'tree' in tree]
    print('tree names', tree_names)

    for tree_name in tree_names:
        if tree_name + '_remodeled.stl' not in os.listdir(os.path.join(stl_folder, 'remodeled_trees')):
            print(tree_name)
            random_tree_model_placement(reference_point, folder_path, tree_name,
                                        object_d_veg)


def get_unique_layers(county, points_buildings=None, points_vegetation=None, points_topography=None):
    unique_d_layers = {}
    if points_buildings:
        unique_d_layers['GML'] = unique_list_coordinates(
            points_buildings, "GML", county)
    if points_vegetation:
        unique_d_layers['DSM'] = unique_list_coordinates(
            points_vegetation, "DSM", county)
    if points_topography:
        unique_d_layers['DTM'] = unique_list_coordinates(
            points_topography, "DTM", county)
    return unique_d_layers


class Distance:
    @classmethod
    def create_distance_list(cls, points_shape, target_building_centroid):
        cls.points_shape = points_shape
        cls.target_building_centroid = target_building_centroid

        distance_list = []
        if any(isinstance(i, list) for i in cls.points_shape[0]):
            for point_cluster in cls.points_shape:
                for point_shape in point_cluster:
                    distance_list.append(np.linalg.norm(
                        np.array(cls.target_building_centroid) - np.array(point_shape)))
        else:
            for point_shape in cls.points_shape:
                distance_list.append(np.linalg.norm(
                    np.array(cls.target_building_centroid) - np.array(point_shape)))
        return distance_list


def distance_max_from_class(points_shape, target_building_centroid):
    """
    This function is used to determine the maximum distance a shape of points and the target building's centroid.
    :param points_shape: Points taken into consideration (e.g. points_buildings, points_topography, points_vegetation).
    :param target_building_centroid: The UTM coordinates of the target building's centroid
    :return maximum_distance: The maximum distance between the shape of points and the centroid.
    """
    distance_list = Distance.create_distance_list(
        points_shape, target_building_centroid)
    maximum_distance = round(max(distance_list), 2)
    return maximum_distance


def post_terrain_objects_cloud(server_address, access_token, project_folder, project_id, alpha_shape_value,
                               target_building_centroid, points_topography):
    """    project_id = 8363
        project_folder = r'G:\Shared drives\Julia\flask\projects\Intercontinental-Duesseldorf'
        server_address = r'https://leaftech-api.dev1.secu-ring.de/api/'

        credentials_d = {"username": 'admin@brayn.io',
                         "password": 'braynio'}
        access_token = obtain_token(credentials_d, server_address)"""

    dtm_folder = os.path.join(project_folder, 'GeospatialData', 'DTM')
    get_terrain_objects = get_request(
        server_address, access_token, "surroundings/terrain", projectId=project_id)
    terrain_objects_list = []
    for terrain_object in get_terrain_objects['list']:
        terrain_objects_list.append(terrain_object['name'])

    get_tb = get_request(server_address, access_token,
                         "surroundings/buildings", projectId=project_id, target='true')
    """    points_topography = [[343894.81, 5676862.05],
                             [343505.34, 5676679.48],
                             [344231.26, 5675990.26],
                             [345384.02, 5675919.49],
                             [345533.27, 5676094.5],
                             [345537.6, 5676537.12],
                             [345804.75, 5676843.18],
                             [345024.45, 5677620.44],
                             [344925.63, 5677922.51],
                             [344323.82, 5678150.09],
                             [344267.36, 5678068.07],
                             [344242.22, 5677832.57],
                             [343894.81, 5676862.05]]
        target_building_centroid = [344791.17, 5676743.39]"""

    max_distance_terrain = distance_max_from_class(
        points_topography, target_building_centroid[:2])

    coordinate_list_int = []
    for file in os.listdir(dtm_folder):
        print("Currently processing:", os.path.join(dtm_folder, file))
        dtm_file = open(os.path.join(dtm_folder, file), encoding='utf8')
        for i in dtm_file:
            unique_coordinate = list(map(float, i.split()))
            if len(str(int(unique_coordinate[0]))) == 8:
                unique_coordinate[0] = float(str(unique_coordinate[0])[2:])
            unique_coordinate[2] = round(unique_coordinate[2] / 2) * 2
            unique_coordinate = list(map(int, unique_coordinate))
            distance = np.linalg.norm(
                np.array(target_building_centroid) - np.array(unique_coordinate[:2]))
            if distance <= max_distance_terrain:
                coordinate_list_int.append(unique_coordinate)
        print(str(len(coordinate_list_int)),
              " belong in the perimeter of concern.")
    point_cloud_array = np.array(coordinate_list_int)

    height_dictionary = dict()

    for unique_coordinates in coordinate_list_int:
        # print(unique_coordinates)
        if unique_coordinates[2] in height_dictionary:
            # append the new number to the existing array at this slot
            height_dictionary[unique_coordinates[2]].append(unique_coordinates)
        else:
            # create a new array in this slot
            height_dictionary[unique_coordinates[2]] = [unique_coordinates]
    height_dictionary.keys()
    print(height_dictionary.keys())

    for height, coordinates in height_dictionary.items():
        print(height, len(coordinates))
        if 'TR_' + str(height) not in terrain_objects_list:
            if height > 0:

                height_array = np.array(coordinates)
                print('1')
                xy_coordinate_array = height_array[:, :2]
                print('2')
                xy_coordinate_list = xy_coordinate_array.tolist()
                print('3')
                alpha_shape1 = alphashape.alphashape(
                    xy_coordinate_list, alpha_shape_value)
                print('4')
                terrain_dict = {"ID": "TR_" + str(height), "surfaces": []}

                counter = 1
                if alpha_shape1.type == 'MultiPolygon':
                    print('5', alpha_shape1.type)
                    for i in alpha_shape1:
                        polygon_array = np.array(i.exterior)
                        print('6')
                        polygon_list = polygon_array.tolist()
                        for k in polygon_list:
                            k.append(height)
                        polygon_list_int = [[int(float(j))
                                             for j in i] for i in polygon_list]
                        result = {"polygon": polygon_list_int, "ID": str(height) + "_" + str(counter),
                                  "type": "Terrain"}
                        print(str(height) + "_" + str(counter))
                        terrain_dict['surfaces'].append(result)
                        counter += 1

                    payload_terrain = {
                        "projectId": project_id,
                        "data": str(terrain_dict['surfaces']),
                        "name": terrain_dict['ID']
                    }
                    payload_terrain_json = json.dumps(payload_terrain)
                    post_request(server_address, access_token,
                                 "surroundings/terrain", payload_terrain_json)

                elif alpha_shape1.type == 'Polygon':
                    print(alpha_shape1.type)
                    polygon_array = np.array(alpha_shape1.exterior)
                    polygon_list = polygon_array.tolist()
                    for k in polygon_list:
                        k.append(height)
                    polygon_list_int = [[int(float(j))
                                         for j in i] for i in polygon_list]
                    result = {"polygon": polygon_list_int, "ID": str(height) + "_" + str(counter),
                              "type": "Terrain"}
                    print(str(height) + "_" + str(counter))
                    terrain_dict['surfaces'].append(result)
                    counter += 1

                    payload_terrain = {
                        "projectId": project_id,
                        "data": str(terrain_dict['surfaces']),
                        "name": terrain_dict['ID']
                    }
                    payload_terrain_json = json.dumps(payload_terrain)
                    post_request(server_address, access_token,
                                 "surroundings/terrain", payload_terrain_json)

                else:
                    polygon_array = np.array(alpha_shape1.coords)
                    polygon_list = polygon_array.tolist()
                    for k in polygon_list:
                        k.append(height)
                    polygon_list_int = [[int(float(j))
                                         for j in i] for i in polygon_list]
                    result = {"polygon": polygon_list_int, "ID": str(height) + "_" + str(counter),
                              "type": "Terrain"}
                    print(str(height) + "_" + str(counter))
                    terrain_dict['surfaces'].append(result)
                    counter += 1

                    payload_terrain = {
                        "projectId": project_id,
                        "data": str(terrain_dict['surfaces']),
                        "name": terrain_dict['ID']
                    }
                    payload_terrain_json = json.dumps(payload_terrain)
                    post_request(server_address, access_token,
                                 "surroundings/terrain", payload_terrain_json)

    return point_cloud_array


def building_utm_center(server_address, access_token, project_id):
    get_tb = get_request(server_address, access_token,
                         "surroundings/buildings", projectId=project_id, target='true')

    x_coordinates_list = []
    y_coordinates_list = []
    z_coordinates_list = []

    for items in get_tb['list']:
        building_dict = ast.literal_eval(items['data'])
        for circle_element in building_dict:
            if circle_element['surface_type'] == 'GROUND':
                polygon = circle_element['polygon']
                x_coordinates_list = [pair[0] for pair in polygon]
                y_coordinates_list = [pair[1] for pair in polygon]
                z_coordinates_list = [pair[2] for pair in polygon]

    x = round(sum(x_coordinates_list) / len(x_coordinates_list), 3)
    y = round(sum(y_coordinates_list) / len(y_coordinates_list), 3)
    z = round(sum(z_coordinates_list) / len(z_coordinates_list), 3)
    building_center = [x, y, z]
    return building_center


def poisson_mesh_triangulation(point_cloud_array, depth, project_folder):
    """
    This function takes a given point cloud (the terrain layer) and returns an array of triangles composed from the
    points in the point cloud. The Poisson reconstruction method for triangulation is used from the Open3d library.

    We transform the point_cloud_array variable type from Numpy to the Open3d o3d.geometry.PointCloud for further
    processing. We first instantiate the Open3d point cloud object, then add points, color and normals to it
    from the original NumPy array.

    After that, we're ready to start the surface reconstruction process by meshing the pcd point cloud. The Poisson
    approach is trying to "envelop" the data in a smooth cloth. There are several parameters available that affect the
    result of the meshing:
    - Which depth? A tree-depth is used for the reconstruction. Higher depth results in a more detailed mesh. A low
    value (between 5 and 7) provides a more smoothing effect, but there is a loss of detail. Higher depth results in
    higher amount of vertices of the generated mesh.
    - Which width? This specifies the target width of the finest level of the tree structure. This parameter is usually
    ignored if the depth is specified.
    - Which scale? It describes the ratio between the diameter of the cube used for reconstruction and the diameter of
    the samples' bounding cube. It is a very abstract parameter, the default value (1.1) usually works well.
    - Which fit? If the linear_fit parameter is set to true, the reconstructor uses linear interpolation to estimate
    the position of the iso-vertices.

    To get the results, we just have to adjust the parameters that we pass to the function. The only parameter that we
    will modify is the depth. The other parameters will remain with the default values.

    At the end, to get a clean result, it is often necessary to add a cropping step to clean unwanted artifacts. For
    this, we compute the initial bounding-box containing the raw point cloud with pcd.get_axis_aligned_bounding_box,
    and we use it to filter all surfaces from the mesh outside the bounding box.

    Exporting the data is straightforward with the write_triangle_mesh function. We just specify within the name of the
    created file, the extension that we want and the mesh to export.

    Finally, we create the triangle list.
    :param point_cloud_array: The point cloud array that we want to triangulate.
    :param depth: Maximum depth of the tree that will be used for surface reconstruction. Running at depth d corresponds
    to solving on a grid whose resolution is no larger than 2^d x 2^d x 2^d. Note that since the reconstructor adapts
    the octree to the sampling density, the specified reconstruction depth is only an upper bound.
    :param project_folder: Directory where the project is stored.
    :return: Triangle array resulting from the mesh.
    """
    if "DigitalTwin" in project_folder:
        output_path = os.path.join(project_folder, "Visualization", "output")
    else:
        output_path = os.path.join(
            project_folder, "DigitalTwin", "Visualization", "output")

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(point_cloud_array)
    pcd.estimate_normals()
    poisson_mesh = \
        o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=depth, width=0, scale=1.1,
                                                                  linear_fit=False)[0]
    bbox = pcd.get_axis_aligned_bounding_box()
    poisson_mesh_crop = poisson_mesh.crop(bbox)
    o3d.io.write_triangle_mesh(os.path.join(output_path, ("poisson_mesh_terrain_depth_" + str(depth) + ".ply")),
                               poisson_mesh_crop)
    vertices_array = np.asarray(poisson_mesh_crop.vertices).tolist()
    triangles_index_position = np.asarray(poisson_mesh_crop.triangles).tolist()

    triangle_list = []
    for i in triangles_index_position:
        triangle_single = []
        for j in i:
            triangle_single.append(vertices_array[j])
        triangle_single.append(triangle_single[0])
        triangle_list.append(triangle_single)
    return triangle_list


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


def calculate_distance_to_target_building(building_center_utm_a, target_building_location_a):
    """
    Calculates the distance between the target building and the examined building.
    :param building_center_utm_a: The UTM coordinates of the surrounding building's center
    :param target_building_location_a: An array containing the latitude and longitude of the target building
    :return: The distance between the two buildings
    """
    target_building_location_utm_a = target_building_location_a
    distance = np.linalg.norm(
        np.array(target_building_location_utm_a) - np.array(building_center_utm_a))
    return distance


def add_to_gml_d(gml_d, target_building_location_a, utm_zone, zone_letter, element, float_a, counter):
    polygon_np_a = np.array_split(np.array(float_a), (len(float_a) / 3))
    polygon_a = []
    for triple in polygon_np_a:
        polygon_a.append(list(triple))

    if element == "GROUND":
        easting = 0
        northing = 0
        for coordinate in polygon_a:
            easting += coordinate[0]
            northing += coordinate[1]
        easting_med = round(easting / len(polygon_a))
        northing_med = round(northing / len(polygon_a))
        building_center_utm_a = [easting_med, northing_med]

        lat_long = utm.to_latlon(
            easting_med, northing_med, utm_zone, zone_letter)
        lat = round(lat_long[0], 7)
        lon = round(lat_long[1], 7)

        gml_d["LatLon"] = [lat, lon]
        gml_d["UTMCenter"] = building_center_utm_a
        gml_d["Distance"] = calculate_distance_to_target_building(building_center_utm_a,
                                                                  target_building_location_a)
    facade_id = element + "_" + str(counter)
    gml_d["surfaces"].append({"polygon": polygon_a,
                              "surface_type": element,
                              "ID": facade_id})

    return gml_d


def parse_line(line, polygon_marker, parsing_d):
    line = line.strip("\n")
    line = line.strip("\t")
    line = line.replace(polygon_marker, "")
    line = line.strip(parsing_d["PolygonEnd"])
    line_a = line.split(" ")
    return line_a


def parse_gml_elements(building_a, building_name, parsing_d, target_building_location_a, perimeter, county):
    """
    :param building_a: The specific building array in a given GML file that is being parsed through.
    :param building_name: The name of the building of concern.
    :param parsing_d: The county specific dictionary that contains data necessary for parsing the GML files.
    :param target_building_location_a: Location of the target building - used to calculate the distance between
    the target building and the building that is currently being parsed.
    :param perimeter: Perimeter around the target building that is being used to take into account the
    buildings that are located within it.
    :param county: County where the target building is located
    :return gml_d: Building specific dictionary containing the ID, LatLon, UTM center, Distance to the
    target building and the surfaces of the building.
    """
    gml_d = {"ID": building_name, "surfaces": []}
    utm_zone = parsing_d["UTMZone"]
    zone_letter = parsing_d["ZoneLetter"]

    for key in parsing_d["Elements"]:
        element = key["ELEMENT"]
        element_marker_start = key["ELEMENTSTART"]
        element_marker_end = key["ELEMENTEND"]
        polygon_marker = parsing_d["PolygonStart"]

        counter = 0
        element_found = False

        for line in building_a:

            if element_marker_start in line:
                element_found = True
                counter += 1
                if county == 'Hamburg':
                    float_a = []

            if polygon_marker in line and element_found:
                if county != 'Hamburg':
                    float_a = []
                line = line.strip("\n")
                line = line.strip("\t")
                line = line.replace(polygon_marker, "")
                line = line.strip(parsing_d["PolygonEnd"])
                line_a = line.split(" ")
                line_a = [el for el in line_a if el != '']

                # line_a = parse_line(line, polygon_marker, parsing_d)
                for coordinate in line_a:
                    float_a.append(float(coordinate))
                if county != 'Hamburg':
                    gml_d = add_to_gml_d(gml_d, target_building_location_a, utm_zone, zone_letter, element,
                                         float_a, counter)

            if element_marker_end in line:
                element_found = False
                if county == 'Hamburg':
                    gml_d = add_to_gml_d(gml_d, target_building_location_a, utm_zone, zone_letter, element,
                                         float_a, counter)
    try:
        if gml_d["Distance"] < perimeter and len(gml_d["surfaces"]) > 1:
            return gml_d
        else:
            return
    except KeyError:
        return


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


def split_gml_cloud(server_address, access_token, project_folder, project_id, county,
                    target_building_centroid, points_buildings, target_shape):
    gml_folder = os.path.join(project_folder, 'GeospatialData', 'GML')
    current_path = os.path.join(INPUT_FILES_FP, 'CountySpecs')
    county_spec_file = os.path.join(current_path, county + '.json')
    with open(county_spec_file, "r") as fp:
        parsing_d = json.load(fp)

    max_distance_buildings = distance_max_from_class(
        points_buildings, target_building_centroid)
    hull_target = hull_check(target_shape)
    hull_surroundings = hull_check(points_buildings)

    get_max_items = get_request(
        server_address, access_token, "surroundings/buildings", projectId=project_id)
    max_items = get_max_items['maxItems']
    if max_items == 0:
        max_items = 1
    get_project_buildings = get_request(server_address, access_token, "surroundings/buildings", projectId=project_id,
                                        limit=max_items)
    building_list = []
    for building in get_project_buildings['list']:
        building_list.append(building['name'])

    target_buildings_list = []
    for tb in building_list:
        if 'TB_' in tb:
            target_buildings_list.append(tb[3:])

    gml_list = os.listdir(gml_folder)
    for gml_file in gml_list:
        gml_file_name = os.path.join(gml_folder, gml_file)
        # "<bldg:Building gml:id="
        building_start_s = parsing_d["BuildingStart"]
        # building ending
        building_end_s = parsing_d["BuildingEnd"]  # "/bldg:Building>"
        gml_load = open(gml_file_name, "r")
        building_found = False
        building_counter = 0
        for line in gml_load:
            if building_start_s in line:
                gml_id = line.strip(" ")
                gml_id = gml_id.strip("\n")
                gml_id = gml_id.replace(building_start_s, "")
                gml_id = gml_id.replace("\"", "")
                gml_id = gml_id.replace(">", "")
                gml_id = gml_id.strip("\t")

                building_found = True
                building_drop_a = []
                building_counter += 1
            # If the end of a building system is found the data is assessed
            # If the building analyzed is in the target perimeter the data will be dumped into a .json file
            if building_end_s in line:
                building_found = False
                gml_d = parse_gml_elements(building_drop_a, gml_id, parsing_d, target_building_centroid,
                                           max_distance_buildings,
                                           county)
                if gml_d is not None:

                    check_points = gml_d['UTMCenter']
                    for i in gml_d['surfaces']:
                        if i['surface_type'] == 'GROUND':
                            check_points.extend(
                                np.array(i['polygon'])[:, :2].tolist())

                    for hull in hull_surroundings:
                        if point_in_polygon(check_points, hull):
                            if "SB_" + gml_d['ID'] not in building_list and gml_d['ID'] not in target_buildings_list:
                                # gml_d['ID'] = "SB_" + gml_d['ID']
                                lat_lon = utm.to_latlon(gml_d['UTMCenter'][0],
                                                        gml_d['UTMCenter'][1],
                                                        32, 'U')
                                surrounding_building_payload = {
                                    "projectId": project_id,
                                    "name": "SB_" + gml_d['ID'],
                                    "quadrant": str(gml_d['UTMCenter'][0])[:3] + '-' + str(gml_d['UTMCenter'][1])[:4],
                                    "latitude": round(lat_lon[0], 4),
                                    "longitude": round(lat_lon[1], 4),
                                    "utmX": gml_d['UTMCenter'][0],
                                    "utmY": gml_d['UTMCenter'][1],
                                    "distance": gml_d['Distance'],
                                    "target": 'false',
                                    "data": str(gml_d['surfaces'])
                                }
                                # print(surrounding_building_payload['name'])
                                payload_surrounding_building_json = json.dumps(
                                    surrounding_building_payload)
                                post_request(server_address, access_token, "surroundings/buildings",
                                             payload_surrounding_building_json)
                                # sb_folder.append(gml_d['ID'])
                                building_list.append("SB_" + gml_d['ID'])
                            else:
                                print(
                                    'surrounding building already exists in the database.', 'id sb', gml_d['ID'])
                    for hull in hull_target:
                        if point_in_polygon(check_points, hull):
                            if "TB_" + gml_d['ID'] not in building_list:
                                # gml_d['ID'] = "TB_" + gml_d['ID']
                                lat_lon = utm.to_latlon(gml_d['UTMCenter'][0],
                                                        gml_d['UTMCenter'][1],
                                                        32, 'U')
                                target_building_payload = {
                                    "projectId": project_id,
                                    "name": "TB_" + gml_d['ID'],
                                    "quadrant": str(gml_d['UTMCenter'][0])[:3] + '-' + str(gml_d['UTMCenter'][1])[:4],
                                    "latitude": round(lat_lon[0], 4),
                                    "longitude": round(lat_lon[1], 4),
                                    "utmX": gml_d['UTMCenter'][0],
                                    "utmY": gml_d['UTMCenter'][1],
                                    "distance": gml_d['Distance'],
                                    "target": 'true',
                                    "data": str(gml_d['surfaces'])
                                }
                                payload_target_building_json = json.dumps(
                                    target_building_payload)
                                post_request(server_address, access_token, "surroundings/buildings",
                                             payload_target_building_json)
                            else:
                                print(
                                    'target building already exists in the database.', 'tb id', gml_d['ID'])
            if building_found:
                building_drop_a.append(line.strip("\n"))


def delete_request(server_address, access_token, table_path, item_id):
    """
    A function that sets up a DELETE request for a given item in the database.
    :param server_address: hostname of the environment where we post the data. We have 3 different environments to
    which the app is being deployed.
    :param access_token: contains the security credentials for a login session and identifies the user, the user's
    groups, the user's privileges, and, in some cases, a particular application. Access tokens only have a limited
    lifetime.
    :param table_path: The specific sub-location of a given table on the server.
    :param item_id: The ID of the item that we want to delete.
    """
    payload_json = {}
    headers = {
        'Authorization': 'Bearer %s' % access_token,
        'Content-Type': 'application/json'
    }
    address = os.path.join(server_address, table_path, str(item_id))
    address = address.replace('\\', '/')
    response = requests.request(
        "DELETE", address, headers=headers, data=payload_json)
    print(response.text.encode('utf8'))


def remove_overlapping_sb(server_address, access_token, project_id):
    get_sb_items = get_request(server_address, access_token, 'surroundings/buildings', projectId=project_id,
                               target='false')
    sb_items = get_sb_items['maxItems']

    get_buildings_s = get_request(server_address, access_token, 'surroundings/buildings', projectId=project_id,
                                  limit=sb_items,
                                  target='false')
    get_buildings_t = get_request(server_address, access_token, 'surroundings/buildings', projectId=project_id,
                                  limit=100,
                                  target='true')
    sb = {}
    for b in get_buildings_s['list']:
        sb[b['name'][3:]] = b['id']

    tb = {}
    for b in get_buildings_t['list']:
        tb[b['name'][3:]] = b['id']

    for key, items in sb.items():
        if key in tb.keys():
            print(key, items)
            delete_request(server_address, access_token,
                           'surroundings/buildings', item_id=str(items))


class Surface:
    def __init__(self, polygon_coordinates):
        self.coordinates = polygon_coordinates  # array of arrays
        self.parameter_form()
        self.format()
        self.angle_calculation_deg()
        self.projecting()

    def format(self):
        """
        Checks the amount of points the polygon consists of
        Can be used to determine whether a polygon is valid or not
        Should be used to exclude short polygons as well as too long ones

        The function first checks if there are 3 or 4 coordinates defining the polygon
        Next it checks if all coordinates are XYZ
        Next it checks if there are any NAN values inside the coordinate)

        Last it checks whether any other issues exist (e.g. Coordinate repetition or similar)
        """
        if len(self.coordinates) < 3:
            print("Not enough coordinates")
            return False
        else:
            for element in self.coordinates:
                if len(element) != 3:
                    print("No XYZ coordinates. Please check data consistency")
                    return False
                else:
                    for digit in element:

                        try:
                            float(digit)
                        except:
                            print(
                                "UTM coordinates are supposed to be numbers. Please check data consistency.")
                            return False
            return True

    def parameter_form(self):
        """
        Generates the parameter of a plain containing the Surface
        This is later used to:
        1) Position the sensors
        2) Determine the perpendicular vector
        3) Normalize the resulting vectors of the parameter_form

        Identifies 3 consecutive points of the polygon which are not in line
        Generates the parameter_form from them.
        Here it is checked if 3 coordinates are on the same line.
        This would be problematic but can be easily done
        """
        point_a = np.array(self.coordinates[0])
        dir_vec_array = []
        norm_dir_vec_array = []
        compare_array = []
        for coordinate in range(len(self.coordinates) - 1):
            compare_array.append(np.array(
                self.coordinates[coordinate]) - np.array(self.coordinates[coordinate + 1]))
            dir_vec = (np.array(
                self.coordinates[coordinate + 1]) - np.array(self.coordinates[coordinate]))
            norm_vec = list(self.norming(dir_vec))

            if np.all((norm_vec == norm_dir_vec_array[:]) is False) and len(norm_dir_vec_array) < 2:
                dir_vec_array.append(dir_vec)
                norm_dir_vec_array.append(norm_vec)

            if np.all(np.array(self.coordinates[coordinate]) == np.array(self.coordinates[coordinate + 1])):
                np.delete(np.array(self.coordinates), [coordinate])

            else:
                print("", end='')

        dir_vec_ab = dir_vec_array[0]
        dir_vec_bc = dir_vec_array[1]

        perpendicular = np.cross(dir_vec_ab, dir_vec_bc)
        norm_perpendicular = self.norming(perpendicular)
        normdir_vec_ab = np.array(norm_dir_vec_array[0])
        normdir_vec_bc = np.array(norm_dir_vec_array[1])

        factor = normdir_vec_ab[0] * normdir_vec_bc[0] + normdir_vec_ab[1] * normdir_vec_bc[1] + normdir_vec_ab[2] * \
            normdir_vec_bc[2]
        intersection = normdir_vec_ab * (factor / (
            np.power(normdir_vec_ab[0], 2) + np.power(normdir_vec_ab[1], 2) + np.power(normdir_vec_ab[2], 2)))
        if intersection[0] == round(0, 0) and intersection[1] == round(0, 0) and intersection[2] == round(0, 0):
            normdir_vec_bc = normdir_vec_bc
        else:
            normdir_vec_bc = normdir_vec_bc - intersection

        self.point_a = point_a
        self.dir_vec_ab = dir_vec_ab
        self.dir_vec_bc = dir_vec_bc
        self.norm_dir_vec_ab = normdir_vec_ab
        self.norm_dir_vec_bc = normdir_vec_bc
        self.norm_perpendicular = norm_perpendicular
        self.len_ab = np.sqrt(
            pow(dir_vec_ab[0], 2) + pow(dir_vec_ab[1], 2) + pow(dir_vec_ab[2], 2))
        self.len_bc = np.sqrt(
            pow(dir_vec_bc[0], 2) + pow(dir_vec_bc[1], 2) + pow(dir_vec_bc[2], 2))
        self.area = round(self.len_ab * self.len_bc, 4)

    def norming(self, Vector):
        """
        Takes the different direction vector which exist and norms them.
        1. Calculate the vector length
        2. Norm the vector
        """
        norm_vector = 1.0 / \
            np.sqrt(pow(Vector[0], 2) + pow(Vector[1], 2) +
                    pow(Vector[2], 2)) * Vector

        return norm_vector

    def angle_calculation_deg(self):
        """
        Takes the normalized direction vector as an np.array and calculates the azimuth and tilt angles in degrees
        The azimuth values go from 0.0 to 360.0
            1. if X is >0 and Y>0 the angel is between 0 and 90;
            2. if X is >0 and Y<0 the angel is between 90 and 180
            3. if X is <0 and Y<0 the angel is between 180 and 270
            4. if x is <0 and Y>0 the angel is between 270 and 360

        The tilt values go from 0.0 to 90.0 ---> currently no tilted overhangs like this: _/  considered.
        As the length of the vector is defined as 1 it can be calculated using the z height
        tilt = np.degrees(np.arccos(vector[2]))
            1. if it is 0 the tilt is 90
            2. if it is 90.0 the tilt is 0
        """

        vector = self.norm_perpendicular

        tilt_f = (np.degrees(np.arccos(vector[2])))
        if tilt_f < 0:
            tilt_f = 0.0
        if tilt_f > 90:
            tilt_f = 0.0

        self.tilt_f = tilt_f

    def projecting(self):
        """
        Projects the surface in the XY, XZ and YZ Area
        Here all meshing steps as well as calculation steps regarding area can be done
        generates a projected polygon with two coordinates only
        """
        # print("\n")
        self.projectedPolygon_a = []

        if self.tilt_f < 80.0:
            self.case = 1
            for point in self.coordinates:
                self.projectedPolygon_a.append([point[0], point[1]])

        else:
            for point in self.coordinates:
                self.projectedPolygon_a.append([point[0], point[2]])
        self.projectedPolygon = self.projectedPolygon_a


def creating_2D_convex_hull(points):
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


def triangulate_tetragon(polygon_a):
    """
    Creates two triangles from a given 3d-planar tetragon
    The last coordinate of the polygon must be the same as the first coordinate
    :param polygon_a: polygon array in the form [[x1,y1,z1],[x2,y2,z2],[...],...]
    :return: triangles_a - an array of arrays of array containing the created 3D Triangles in [X,Y,Z] coordinates
    """
    triangle_1 = polygon_a[:3]
    triangle_1.append(triangle_1[0])

    triangle_2 = polygon_a[2:]
    triangle_2.append(triangle_2[0])
    triangles_a = [triangle_1, triangle_2]
    return triangles_a


def triangulate_polygon_with_higher_than_5_points(polygon_a):
    """
    Function that is used to triangulate polygons that have arrays with more than 5 points. For this purpose, the
    Delaunay meshing method is being used.
    :param polygon_a: The array of the polygon that we want to mesh
    :return: Array of arrays that contain the individual triangles resulting from the meshing.
    """
    new_surface = Surface(polygon_a)
    projected_polygon = new_surface.projectedPolygon
    delaunay_mesh = Delaunay(projected_polygon)
    mesh_simplices = delaunay_mesh.simplices

    meshed_triangles = []
    for simplex in mesh_simplices:
        meshed_individual = []
        for position in simplex:
            meshed_individual.append(polygon_a[position])
        meshed_individual.append(polygon_a[simplex[0]])
        # if Polygon(projected_polygon).is_valid:
        if Polygon(meshed_individual).within(Polygon(projected_polygon)):
            meshed_triangles.append(meshed_individual)
        else:
            print('invalid polygon')
    return meshed_triangles


def triangulate_static_shading_influences_cloud(project_folder, server_address, access_token, project_id, target):
    """
    This function takes the buildings of a given project and triangulates the surfaces of the buildings.
    The method used for triangulation depends on the number of points that the array of a given surface has. If there
    are 5 points in the surface, we use the triangulate_tetragon function which splits the surface in two triangles.
    If the array has 4 points, and the first one and the last one are the same, that surface is already a triangle. If
    the array has more than 5 points, we use the triangulate_polygon_with_higher_than_5_points, which uses the Delaunay
    triangulation method.

    Additionally, if we have invalid surface polygons, they are all stored in a dictionary for further review.

    :param project_folder:
    :param target: True/False, depending on whether we want to triangulate target or surrounding buildings.
    :param server_address: hostname of the environment where we post the data. We have 3 different environments to
    which the app is being deployed.
    :param access_token: contains the security credentials for a login session and identifies the user, the user's
    groups, the user's privileges, and, in some cases, a particular application. Access tokens only have a limited
    lifetime.
    :param project_id: The id of the project in the database.
    :return: Array of arrays that contains the resulting triangles.
    """
    get_max_items = get_request(server_address, access_token, "surroundings/buildings", projectId=project_id,
                                target=target)
    maxItems = get_max_items['maxItems']
    get_buildings = get_request(server_address, access_token, "surroundings/buildings", projectId=project_id,
                                limit=maxItems, target=target)

    triangles_static_l = []
    faulty_polygons_total = {}
    for items in get_buildings['list']:
        surfaces = ast.literal_eval(items['data'])
        faulty_polygons_total[items['name']] = []
        for surface_elements in surfaces:
            polygon = surface_elements['polygon']
            polygon_instance = Surface(polygon)
            projected_polygon = polygon_instance.projectedPolygon
            if not Polygon(projected_polygon).is_valid:
                # print(surface_elements['ID'])
                if polygon_instance.tilt_f < 80.0:
                    # print(items['name'], surface_elements['ID'])
                    projected_polygon = creating_2D_convex_hull(
                        projected_polygon)
            if Polygon(projected_polygon).is_valid:
                if len(polygon) == 5:
                    triangles_a = triangulate_tetragon(polygon)
                    triangles_static_l.append(triangles_a[0])
                    triangles_static_l.append(triangles_a[1])

                if len(polygon) < 5:
                    triangles_static_l.append(polygon)

                if len(polygon) > 5:
                    tri_lists = triangulate_polygon_with_higher_than_5_points(
                        polygon)
                    for a in tri_lists:
                        triangles_static_l.append(a)
            elif not Polygon(polygon).is_valid:
                # print(Polygon(polygon).is_valid, polygon, items['name'], surface_elements['ID'])
                # print('fp', faulty_polygons_total)
                faulty_polygons_total[items['name']].append(surface_elements)

    empty_keys = []
    for key in faulty_polygons_total.keys():
        if not faulty_polygons_total[key]:
            empty_keys.append(key)
    for empty_key in empty_keys:
        del faulty_polygons_total[empty_key]

    if 'DigitalTwin' in project_folder:
        faulty_polygons_fp = os.path.join(project_folder, "FaultyPolygons")
    else:
        faulty_polygons_fp = os.path.join(
            project_folder, "DigitalTwin", "FaultyPolygons")
    with open(os.path.join(faulty_polygons_fp, 'faulty_polygons.json'), 'w') as f:
        json.dump(faulty_polygons_total, f)
    print('The faulty polygons have been stored in the project folder.')

    return triangles_static_l


"""main_project_folder = r'G:\Shared drives\04_Sales_and_Operations\03_Operations\Twin_Hatten\Vattenfall_group'
server_address = 'https://leaftech-api.dev1.secu-ring.de/api/'
username = 'admin@brayn.io'
password = 'braynio'
credentials_d = {'username': username, 'password': password}
access_token = obtain_token(credentials_d, server_address)

# customer_id = customer_setup('Michael', 'en', server_address, access_token)
customer_id = 25
for project in os.listdir(main_project_folder):
    if '- error' in project:
        print(project)
        project_folder = os.path.join(main_project_folder, project)
        config_file = read_json_files(os.path.join(project_folder, 'DigitalTwin', 'config'))
        project_id = project_setup(config_file, customer_id, server_address, access_token)
        print(project_id)
        cad_geo_adjustments(project_folder, project_id, server_address, access_token, 8, 0.04, 0.4)
"""


def project_setup(config_file, customer_id, server_address, access_token):
    get_existing_projects = get_request(
        server_address, access_token, 'projects', limit=10000)['list']
    existing_projects_d = {project['name']: project['id']
                           for project in get_existing_projects}
    if config_file['ProjectName'] in existing_projects_d:
        project_id = existing_projects_d[config_file['ProjectName']]
        return project_id
    else:
        if config_file['WeatherAPI'] == 'off':
            processing = 'false'
        else:
            processing = 'true'
        payload_project_data = dumps({
            'name': config_file['ProjectName'],
            'street': config_file['street'],
            'postCode': config_file['postCode'],
            'city': config_file['city'],
            'country': config_file['Country'],
            'processing': processing,
            'customerId': customer_id,
            'referenceLongitude': 15,
            'language': config_file['Language']
        })
        print(payload_project_data)
        project = post_request(server_address, access_token,
                               "projects", payload_project_data)
        print(project)
        project_id = project['id']

        return project_id


def customer_setup(customer_name, customer_language, server_address, access_token):
    print('server address', server_address)
    get_existing_customers = get_request(
        server_address, access_token, "customer", limit=10000)['list']
    existing_customer_d = {customer['name']: customer['id']
                           for customer in get_existing_customers}
    if customer_name in existing_customer_d:
        customer_id = existing_customer_d[customer_name]
        return customer_id

    else:
        if customer_language == 'English':
            customer_language = 'en'
        else:
            customer_language = 'de'
        customer_payload = {
            "language": customer_language,
            "name": customer_name
        }
        customer_payload_json = dumps(customer_payload)
        post_customer = post_request(
            server_address, access_token, 'customer', customer_payload_json, printing=True)
        customer_id = post_customer['id']
        return customer_id


def import_stl(mesh_file):
    triangles_meshed = np.empty(len(mesh_file), dtype=object)
    for position, data in enumerate(mesh_file.data):
        data_new = data[1].tolist()
        data_new.append(data[1][0].tolist())
        data_new_a = np.array(data_new)
        triangles_meshed[position] = data_new_a
    return triangles_meshed
