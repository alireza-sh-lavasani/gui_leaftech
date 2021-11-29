import os
import requests
import shutil
import time
import gzip
import zipfile
from subprocess import call


def geo_data_download(project_folder, county, unique_list_layers):
    dir_path = r"/Users/jules/Downloads"
    download_start_time = None
    r = None
    filename = None

    if county == 'Hamburg':
        gml_base = r"G:\Shared drives\CityGML-DataBase\Germany\Hamburg"
        dsm_base = r"G:\Shared drives\CityGML-DataBase\Germany\Hamburg_surface"
        dtm_base = r"G:\Shared drives\CityGML-DataBase\Germany\Hamburg_surface"

        gml_folder = os.path.join(project_folder, 'GeospatialData', 'GML')
        dtm_folder = os.path.join(project_folder, 'GeospatialData', 'DTM')
        dsm_folder = os.path.join(project_folder, 'GeospatialData', 'DSM')

        for layer in unique_list_layers:
            for key in layer:
                print(key)
                for x in layer[key][0]:
                    for y in layer[key][1]:
                        zip_file_addon = str(x) + "_" + str(y)
                        if key == 'GML':
                            for i in os.listdir(gml_base):
                                if i[5:13] == zip_file_addon:
                                    print(zip_file_addon)
                                    shutil.copy2(os.path.join(
                                        gml_base, i), gml_folder)
                        if key == 'DSM':
                            for i in os.listdir(dsm_base):
                                if i[7:15] == zip_file_addon:
                                    print(zip_file_addon)
                                    shutil.copy2(os.path.join(
                                        dsm_base, i), dsm_folder)
                        if key == 'DTM':
                            for i in os.listdir(dtm_base):
                                if i[7:15] == zip_file_addon:
                                    print(zip_file_addon)
                                    shutil.copy2(os.path.join(
                                        dtm_base, i), dtm_folder)

    if county == 'Brandenburg':
        url_base = r"https://data.geobasis-bb.de/geobasis/daten/"
        zip_file_joining_character = '-'
        gml_url_base = os.path.join(url_base, '3d_gebaeude/lod2_gml/lod2_33')
        gml_zip_base = 'lod2_33'
        gml_appendix = '.zip'
        dsm_url_base = os.path.join(url_base, 'bdom/xyz/bdom_33')
        dsm_zip_base = 'bdom_33'
        dsm_appendix = '.zip'
        dtm_url_base = os.path.join(url_base, 'dgm/xyz/dgm_33')
        dtm_zip_base = 'dgm_33'
        dtm_appendix = '.zip'

    elif county == 'Sachsen':
        url_base = r"https://geocloud.landesvermessung.sachsen.de/index.php/s/"
        zip_file_joining_character = ''
        gml_url_base = os.path.join(
            url_base, '3XKFZqznzR2PrFk/download?path=%2F&files=lod2_33')
        gml_zip_base = 'lod2_33'
        gml_appendix = '_2_sn_citygml.zip'
        dsm_url_base = os.path.join(
            url_base, 'w7LQy9F6Yo3IxPp/download?path=%2F&files=dom1_')
        dsm_zip_base = 'dom1_'
        dsm_appendix = '.zip'
        dtm_url_base = os.path.join(
            url_base, 'DK9AshAQX7G1bsp/download?path=%2F&files=dgm1_')
        dtm_zip_base = 'dgm1_'
        dtm_appendix = '.zip'

    elif county == 'Berlin':
        url_base = r"http://fbinter.stadt-berlin.de/fb/atom/"
        zip_file_joining_character = '_'
        gml_url_base = os.path.join(url_base, 'LOD2/LoD2_')
        gml_zip_base = 'LoD2_'
        gml_appendix = '.zip'
        dsm_url_base = os.path.join(url_base, 'bDOM1/')
        dsm_zip_base = ''
        dsm_appendix = '.zip'
        dtm_url_base = os.path.join(url_base, 'DGM1/')
        dtm_zip_base = ''
        dtm_appendix = '.zip'

    elif county == 'NRW' or county == 'Nordrhein-Westfalen':
        url_base = r"https://www.opengeodata.nrw.de/produkte/geobasis/"
        zip_file_joining_character = '_'
        gml_url_base = os.path.join(url_base, '3dg/lod2_gml/lod2_gml/LoD2_32_')
        gml_zip_base = ''
        gml_appendix = '_1_NW.gml'
        dsm_url_base = os.path.join(url_base, 'hm/3dm_l_las/3dm_l_las/3dm_32_')
        dsm_zip_base = ''
        dsm_appendix = '_1_nw.laz'
        dtm_url_base = os.path.join(url_base, 'hm/dgm1_xyz/dgm1_xyz/dgm1_32_')
        dtm_zip_base = 'dgm1_32_'
        dtm_appendix = '_1_nw.xyz.gz'

    for layer in unique_list_layers:
        for key in layer:
            print('\n')
            print(key, ' files are being downloaded from:')

            folder = os.path.join(project_folder, 'GeospatialData', key)
            if key == 'GML':
                key_list = [gml_url_base, gml_zip_base, gml_appendix, folder]
                file_appendix = '.gml'
                # exceptions to previous setup
                if county == 'Sachsen':
                    zip_file_joining_character = '_'
            elif key == 'DSM':
                key_list = [dsm_url_base, dsm_zip_base, dsm_appendix, folder]
                file_appendix = '.xyz'
                # exceptions
                if county == 'NRW' or county == 'Nordrhein-Westfalen':
                    file_appendix = '.txt'
            elif key == 'DTM':
                key_list = [dtm_url_base, dtm_zip_base, dtm_appendix, folder]
                file_appendix = '.xyz'
                # exceptions
                if county == 'Berlin' or county == 'NRW' or county == 'Nordrhein-Westfalen':
                    file_appendix = '.txt'

            # print("key: %s , value: %s" % (key, layer[key]))

            for x in layer[key][0]:
                for y in layer[key][1]:
                    final_name = str(x) + "_" + str(y) + file_appendix
                    final_path = os.path.join(folder, final_name)
                    zip_file_addon = str(
                        x) + zip_file_joining_character + str(y)
                    zip_file_name = key_list[1] + zip_file_addon + key_list[2]
                    download_url_name = key_list[0] + \
                        zip_file_addon + key_list[2]
                    download_start_time = time.time()
                    print(download_url_name)
                    r = requests.get(download_url_name)
                    zip_filepath = os.path.join(key_list[3], zip_file_name)

                    if r.status_code == 200:
                        print("File is successfully downloaded in", round(time.time() - download_start_time, 1),
                              "seconds")
                        with open(zip_filepath, 'wb') as f:
                            f.write(r.content)

                        if key_list[2].endswith('.zip'):
                            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                                zip_ref.extractall(key_list[3])
                        if key_list[2].endswith('.gz'):
                            with gzip.open(os.path.join(zip_filepath), 'rb') as f_in:
                                with open(os.path.join(final_path), 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                        # check with Rato if this works
                        if key_list[2].endswith('.laz'):
                            cmdline = r'laszip.exe -i "{}" -otxt -oparse xyz'.format(
                                filename.replace("//", "\\"))
                            rc = call("start cmd /K " + cmdline,
                                      cwd=dir_path, shell=True)

                        for filename in os.listdir(folder):
                            filename_path = os.path.join(folder, filename)
                            if filename.endswith(file_appendix):
                                os.rename(filename_path, final_path)
                            else:
                                os.remove(filename_path)
