

def append_to_the_lists(list_easting, list_northing, points):
    if any(isinstance(i, list) for i in points[0]):
        for point_cluster in points:
            for point in point_cluster:
                list_easting.append(str(point[0])[:3])
                list_northing.append(str(point[1])[:4])
    else:
        for point in points:
            list_easting.append(str(point[0])[:3])
            list_northing.append(str(point[1])[:4])
    return list_easting, list_northing


def get_unique_list_nrw(list_coordinates):
    unique_list = list(set(list_coordinates))
    evens = []
    for i in unique_list:
        evens.append(i)
    unique_list_nrw = list(set(evens))
    return unique_list_nrw


def get_unique_list_evens(list_coordinates):
    unique_list = list(set(list_coordinates))
    evens = []
    for i in unique_list:
        if int(float(i)) % 2 == 0:
            evens.append(i)
        else:
            i = str(int(float(i)) - 1)
            evens.append(i)
    unique_list_hamburg = list(set(evens))
    return unique_list_hamburg


def unique_list_coordinates(points, file_type, county):
    """
    This function takes the points all the points contained in a given data type, only to extract the first 3 digits of
    the Easting UTM coordinate and the first 4 digits of the Northing UTM coordinate. This is done because for each
    of the downloadable counties, the data is stored in a way that is county specific, yet always contains these digits
    as unique identifiers. What is also county specific, is the way the data is stored. In some, the UTM pairings
    account for only the even numbers of the Easting coordinate digits (e.g. 390-2824, 392-2824), while in some case
    all the numbers of the Easting coordinate digits are considered (e.g. 390-2824, 391-2824). This function addresses
    county specific variations.
    :param points: Points taken into consideration (e.g. points_buildings, points_topography, points_vegetation).
    :param file_type: The type of data that is being parsed (GML, DSM or DTM)
    :param county: The county where the project is located
    :return unique_list: A unique list of coordinate pairings is returned.
    """

    list_easting = []
    list_northing = []
    unique_list_easting = None
    unique_list_northing = None
    unique_list = None
    if county == 'NRW':
        if file_type == 'DTM':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = get_unique_list_nrw(list_easting)
            unique_list_northing = get_unique_list_nrw(list_northing)

        elif file_type == 'DSM':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = list(set(list_easting))
            unique_list_northing = list(set(list_northing))
        elif file_type == 'GML':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)

            unique_list_easting = list(set(list_easting))
            unique_list_northing = list(set(list_northing))
        unique_list = [unique_list_easting, unique_list_northing]

    if county == 'Hamburg':
        if file_type == 'DTM':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = get_unique_list_evens(list_easting)
            unique_list_northing = get_unique_list_evens(list_northing)
        elif file_type == 'DSM':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = get_unique_list_evens(list_easting)
            unique_list_northing = get_unique_list_evens(list_northing)
        elif file_type == 'GML':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)

            unique_list_easting = list(set(list_easting))
            unique_list_northing = list(set(list_northing))
        unique_list = [unique_list_easting, unique_list_northing]

    elif county == 'Berlin':
        if file_type == 'DTM':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = get_unique_list_evens(list_easting)
            unique_list_northing = get_unique_list_evens(list_northing)
        elif file_type == 'DSM':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = get_unique_list_evens(list_easting)
            unique_list_northing = get_unique_list_evens(list_northing)
        elif file_type == 'GML':
            list_easting, list_northing = append_to_the_lists(list_easting, list_northing, points)
            unique_list_easting = get_unique_list_evens(list_easting)
            unique_list_northing = get_unique_list_evens(list_northing)
        unique_list = [unique_list_easting, unique_list_northing]
    return unique_list
