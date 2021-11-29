import json


def read_json_files(file_path):
    """
    Reads a json file from a given file_path
    :param file_path: the path of the file that needs to be loaded
    :return: the json dictionary is returned
    """
    json_filename = str(file_path)
    with open(json_filename, 'r') as fp:
        dict_d = json.load(fp)
    return dict_d
