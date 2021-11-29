import matplotlib
import os
from flask import Flask, render_template, request, send_from_directory
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from app_functions import manual_stl_download, automatic_stl_download, geo_data_download, \
    setup_project, get_menu_checklist, return_config_dict, write_config_dict, select_geo_template, \
    return_building_dict, write_building_dict, obtain_token, get_request, customer_setup, \
    project_setup, read_json_files, get_relevant_data, get_unique_layers, post_terrain_objects_cloud, \
    poisson_mesh_triangulation, building_utm_center, triangle_norming, export_stl, split_gml_cloud, \
    remove_overlapping_sb, triangulate_static_shading_influences_cloud, get_object_d_vegetation

projects_list = []
folder_name = 'folder'
access_token = 'token'
destination_path = ''

config_file = {}
selected_environment = 'environment'
project_id = 0

PATH = os.getcwd()
print('current cwd', PATH)
INPUT_FILES_FP = os.path.join(PATH, 'data')
CATEGORY_DICT = os.path.join(INPUT_FILES_FP, 'category_d.json')

matplotlib.use("Agg")

app = Flask(__name__)

if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


@app.route("/")  # default page
def index():
    return render_template('home.html', error=False)


@app.route("/login_page", methods=['POST'])  # process the login page
def login_page():
    global access_token
    global selected_environment
    global projects_list
    global destination_path
    if request.method == 'POST':
        selected_environment = request.form['environment_selection']
        username = request.form['username']
        password = request.form['password']

        credentials_d = {"username": username,
                         "password": password}
        access_token = obtain_token(credentials_d, selected_environment)

        if access_token:
            projects = get_request(
                selected_environment, access_token, 'projects', limit=10000)['list']
            projects_list = [project['name'] for project in projects]
            return render_template('setup_2_0.html', project_list=projects_list, error=False)
        else:
            return render_template('home.html', error=True)


# define new project or load old project
@app.route("/project_selection", methods=['POST'])
def project_selection():
    global selected_environment
    global access_token
    global folder_name
    global destination_path
    checklist = None
    project_name = None
    if request.method == 'POST':
        form_project_name = request.form['form_project_name']

        if form_project_name == 'new_project':
            project_name = request.form['new_project_name']
            if project_name in projects_list or project_name == "":
                return render_template('setup_2_0.html', project_list=projects_list, error=True)
            else:
                folder_name = project_name.replace(" ", "_")
                destination_path = setup_project(project_name)
        else:
            project_name = form_project_name
            folder_name = project_name.replace(" ", "_")

            # shared_folders_name = os.getcwd().split('07_Technology')[0]
            # destination_path = os.path.join(shared_folders_name, '04_Sales_and_Operations', '03_Operations', 'Twin_Hatten',
            #                                 folder_name)

            """
              Create projects folders in the root of the project 
              and create a folder named project_name inside
            """
            destination_path = os.path.join(
                os.getcwd(), 'projects', folder_name)

        # create list indicating whether menu tasks have been done
        checklist = get_menu_checklist(destination_path)

    return render_template('setup_3_0.html', checklist=checklist, project_name=project_name)


@app.route("/go_to_3_1")  # go to project configuration
def go_to_3_1():
    global destination_path
    config_dict = return_config_dict(destination_path)
    return render_template('setup_3_1.html', config_dict=config_dict)


@app.route("/go_to_3_2")  # go to kml setup
def go_to_3_2():
    return render_template('setup_3_2.html', error=False)


@app.route("/go_to_geo_1_0")  # go to geodata page
def go_to_geo_1_0():
    global destination_path
    county, geo_template, geo_info, checklist = select_geo_template(
        destination_path)
    county = county.upper()
    if geo_template == 0:
        return render_template('geo_1_0.html', county=county, checklist=checklist)
    elif geo_template == 1:
        return render_template('geo_1_1.html', county=county, checklist=checklist, geo_info=geo_info)


@app.route("/go_to_terrain_1_0")  # go to terrain set up page
def go_to_terrain_1_0():
    return render_template('terrain_1_0.html')


@app.route("/go_to_buildings_1_0")  # go to buildings set up page
def go_to_buildings_1_0():
    return render_template('buildings_1_0.html')


@app.route("/go_to_trees_1_0")  # go to trees page
def go_to_trees_1_0():
    return render_template('trees_1_0.html')


@app.route("/go_to_cad_1_0")  # go to building page
def go_to_cad_1_0():
    global folder_name
    building_dict = return_building_dict(folder_name)
    return render_template('cad_1_0.html', building_dict=building_dict)


@app.route("/return_to_menu")  # return to the main menu
def return_to_menu():
    global destination_path
    print('folder name', destination_path)
    config_dict = return_config_dict(destination_path)
    project_name = config_dict['ProjectName']
    checklist = get_menu_checklist(os.path.join(destination_path))
    return render_template('setup_3_0.html', checklist=checklist, project_name=project_name)


# process project configuration form
@app.route("/project_configuration", methods=['POST'])
def project_configuration():
    global destination_path
    global selected_environment
    global access_token
    global config_file
    global project_id
    if request.method == 'POST':
        config_file = return_config_dict(destination_path)
        config_file['CustomerName'] = request.form['CustomerName']
        config_file['Language'] = request.form['Language']
        customer_id = customer_setup(request.form['CustomerName'], request.form['Language'], selected_environment,
                                     access_token)
        services = []
        if request.form.get('forecast') == 'checked':
            services.append('forecast')
        if request.form.get('shading') == 'checked':
            services.append('shading')
        if request.form.get('solar') == 'checked':
            services.append('solar')

        config_file['services'] = services
        config_file['WeatherAPI'] = request.form['WeatherAPI']

        location = request.form['Location'][1:-1]
        location_array_str = location.split(", ")
        location_array = [float(coordinate)
                          for coordinate in location_array_str]
        config_file['Location'] = location_array
        config_file['PartnerName'] = request.form['PartnerName']
        config_file['Country'] = request.form['Country']
        config_file['County'] = request.form['County']
        if request.form['County'] == 'Nordrhein-Westfalen':
            config_file['County'] = 'NRW'
        config_file['street'] = request.form['street']
        config_file['postCode'] = int(request.form['postCode'])
        config_file['city'] = request.form['city']
        config_file['WeatherAPI'] = request.form['WeatherAPI']
        project_id = project_setup(
            config_file, customer_id, selected_environment, access_token)
        config_file['ProjectID'] = project_id
        write_config_dict(config_file, destination_path)
    return render_template('setup_3_2.html', error=False)


# later: check the kml file to see if it's accepted
@app.route("/kml_setup", methods=['POST'])  # accept the kml file and save it
def kml_setup():
    global destination_path
    if request.method == 'POST':
        file = request.files['kml_file']
        filename = (secure_filename(file.filename))
        folder_path = os.path.join(destination_path, 'GeospatialData', 'KML')
        file.save(os.path.join(folder_path, filename))
        county, template_option, geo_info, checklist = select_geo_template(
            destination_path)
        if template_option == 0:
            buttonText = 'Download Files'
            return render_template('geo_1_0.html', county=county, checklist=checklist)
        elif template_option == 1:
            return render_template('geo_1_1.html', county=county, checklist=checklist, geo_info=geo_info)


# download geodata for Berlin, NRW, Hamburg, Sachsen
@app.route("/acquire_geodata_download")
def acquire_geodata_download():
    global folder_name
    global config_file
    global destination_path
    # global points_topography
    project_folder = destination_path
    config_file = read_json_files(os.path.join(
        project_folder, 'DigitalTwin', 'config'))
    category_d = read_json_files(CATEGORY_DICT)
    county = config_file['County']
    kml_file = os.listdir(os.path.join(project_folder, 'GeospatialData', 'KML'))
    kml_file_path = os.path.join(
        project_folder, 'GeospatialData', 'KML', kml_file[0])

    tb_center, pts_bldgs, pts_veg, pts_terrain, object_d_veg, target_shape, target_area_shape, target_area_center = \
        get_relevant_data(kml_file_path, category_d)

    unique_list_layers = get_unique_layers(
        county, pts_bldgs, pts_veg, pts_terrain)
    # files download, dependent on the county and the type of data that we download.
    geo_data_download(project_folder, county, unique_list_layers)
    return render_template('buildings_1_0.html')


@app.route("/terrain_1_0")
def terrain_1_0():
    global selected_environment
    global destination_path
    global access_token
    global project_id
    project_folder = destination_path
    category_d = read_json_files(CATEGORY_DICT)

    kml_file = os.listdir(os.path.join(
        project_folder, 'GeospatialData', 'KML'))
    kml_file_path = os.path.join(
        project_folder, 'GeospatialData', 'KML', kml_file[0])

    tb_center, pts_bldgs, pts_veg, pts_terrain, object_d_veg, target_shape, target_area_shape, target_area_center = \
        get_relevant_data(kml_file_path, category_d)

    # methods to generate terrain STL files
    alpha_shape_value = 0.04
    terrain_detail = 8
    point_cloud_terrain = post_terrain_objects_cloud(selected_environment, access_token, project_folder, project_id,
                                                     alpha_shape_value, tb_center, pts_terrain)

    triangle_list_terrain = poisson_mesh_triangulation(
        point_cloud_terrain, terrain_detail, project_folder)
    utm_center = building_utm_center(
        selected_environment, access_token, project_id)
    triangles_terrain_a_normed = triangle_norming(
        triangle_list_terrain, utm_center)
    export_stl(project_folder, triangles_terrain_a_normed, "Terrain")

    return render_template('trees_1_0.html')


@app.route("/buildings_1_0")
def buildings_1_0():
    global selected_environment
    global destination_path
    global config_file
    global project_id
    project_folder = destination_path
    config_file = read_json_files(os.path.join(
        project_folder, 'DigitalTwin', 'config'))
    project_id = config_file['ProjectID']
    county = config_file['County']
    # methods to generate terrain STL files
    category_d = read_json_files(CATEGORY_DICT)

    kml_file = os.listdir(os.path.join(
        project_folder, 'GeospatialData', 'KML'))
    kml_file_path = os.path.join(
        project_folder, 'GeospatialData', 'KML', kml_file[0])

    tb_center, pts_bldgs, pts_veg, pts_terrain, object_d_veg, target_shape, target_area_shape, target_area_center = \
        get_relevant_data(kml_file_path, category_d)

    split_gml_cloud(selected_environment, access_token, project_folder, project_id, county, tb_center,
                    pts_bldgs, target_shape)
    remove_overlapping_sb(selected_environment, access_token, project_id)

    triangles_target_buildings_a = triangulate_static_shading_influences_cloud(
        project_folder,
        selected_environment,
        access_token,
        project_id,
        'true')
    triangles_surrounding_buildings_a = triangulate_static_shading_influences_cloud(
        project_folder,
        selected_environment,
        access_token,
        project_id,
        'false')
    utm_center = building_utm_center(
        selected_environment, access_token, project_id)
    config_file['Location'] = list(utm_center)
    write_config_dict(config_file, folder_name)

    triangles_target_buildings_a_normed = triangle_norming(
        triangles_target_buildings_a, utm_center)
    triangles_surrounding_buildings_a_normed = triangle_norming(triangles_surrounding_buildings_a,
                                                                utm_center)
    triangles_buildings_a_normed = triangles_target_buildings_a_normed + \
        triangles_surrounding_buildings_a_normed
    export_stl(project_folder, triangles_target_buildings_a_normed,
               "Target_Buildings")
    export_stl(project_folder, triangles_surrounding_buildings_a_normed,
               "Surrounding_Buildings")
    export_stl(project_folder, triangles_buildings_a_normed, "Buildings")
    return render_template('terrain_1_0.html')


# choose whether tree is manual or automatic
@app.route("/trees_1_0", methods=['POST'])
def trees_1_0():
    if request.method == 'POST':
        method_type = request.form['method_type']
        if method_type == 'manual':
            tree_fp = os.listdir(os.path.join(PATH, 'static', 'tree_stl'))
            trees_list = [tree.split('.stl')[0]
                          for tree in tree_fp if '.stl' in tree]
            return render_template('trees_2_0.html', tree_list=trees_list)
        elif method_type == 'automatic':
            return render_template('trees_2_1.html')


@app.route('/manual_form', methods=['POST'])  # process manual tree generation
def manual_form():
    global selected_environment
    global destination_path
    global access_token
    global project_id

    path_to_tree = None
    if request.method == 'POST':
        model_tree = request.form['tree_type']
        print('model tree', model_tree)
        object_d_veg = get_object_d_vegetation(destination_path)
        reference_point = read_json_files(os.path.join(
            destination_path, 'DigitalTwin', 'config'))['Location']

        manual_stl_download(destination_path, reference_point,
                            model_tree, object_d_veg)
    return render_template('trees_3_0.html', filepath=path_to_tree)


# process automatic tree generation
@app.route('/automatic_form', methods=['POST'])
def automatic_form():
    global selected_environment
    global folder_name
    global destination_path
    global access_token
    global project_id
    if request.method == 'POST':
        reference_point = read_json_files(os.path.join(
            destination_path, 'DigitalTwin', 'config'))['Location']
        automatic_stl_download(destination_path, reference_point)
    return render_template('trees_3_0.html')


@app.route('/download_stl/<path:filename>')  # download the stl file
def get_file(filename):
    try:
        return send_from_directory('', filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@app.route('/building_configuration', methods=['POST'])
def building_configuration():
    global folder_name
    if request.method == 'POST':
        building_config = return_building_dict(folder_name)
        for key in building_config:
            building_config[key] = request.form[key]
        write_building_dict(building_config, folder_name,
                            'building_config.txt')
        return render_template('trees_1_0.html')


if __name__ == "__main__":
    app.run(debug=True)
