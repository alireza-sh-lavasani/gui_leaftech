import numpy as np

def get_relevant_data(json_dict):
    """
    This function takes a previously constructed json dictionary (in the polygon_from_KML function) that contains data
    from the KML file about the four layers of information (Target buildings, surrounding buildings, vegetation,
    terrain). From this dictionary, specific information is extracted that is necessary for the further setup of the
    project.
    :param json_dict: JSON dictionary containing project specific information about the layers of information.
    :return centroid_point_target_bldg, points_buildings, points_vegetation, points_topography, object_d_vegetation,
    target_shape: There are multiple returns from this function: the centroid point of the target building,
    the points from the buildings, vegetation and topography, the vegetation object dictionary and the target building
    shape.
    """
    target_building_center = []
    points_buildings = []
    points_vegetation = []
    points_topography = []
    centroid_point_target_bldg = []
    target_shape = []
    object_d_vegetation = {'objects': []}
    for i in json_dict['objects']:
        if i['TYPE'] == 'SurroundingBuildings':
            points_buildings.append(i['shape'])
        if i['TYPE'] == 'TargetBuilding':
            target_building_center.append(i['centroid'])
            # print('TARGET BUILDING CENTER', i['centroid'])
            # print(target_bldg_center)
            points_buildings.append(i['shape'])
            centroid_point_target_bldg = np.array(target_building_center[0])
            # print('CENTROID TARGET BUILDING', centroid_point_target_bldg)
            target_shape.append(i['shape'])
        if i['TYPE'] == 'Vegetation':
            object_d_vegetation['objects'].append(i)
            points_vegetation.append(i['shape'])
        if i['TYPE'] == 'Topography':
            points_topography = i['shape']
        # print('points topography', points_topography)
    return centroid_point_target_bldg, points_buildings, points_vegetation, points_topography, object_d_vegetation, \
           target_shape