# --------------------------------
# Name:         build_static_files_for_gages.py
# Purpose:      Build static files for ET-Demands from zonal stats ETCells (basin zone from GAGES-II)
# --------------------------------

import argparse
import copy
from collections import defaultdict
import datetime as dt
import logging
import os
import re
import shutil
import sys

import pandas as pd
from src.prep import _arcpy
from src.config.config_prep import cfg_prep


def main(area_threshold=0.25, beef_cuttings=4, dairy_cuttings=5, overwrite_flag=False):
    """Build static text files needed to run ET-Demands model

    Parameters
    ----------
    area_threshold : float
        CDL area threshold [acres] (the default is 0.25 acres).
    beef_cuttings : int
        Initial number of beef hay cuttings (the default is 4).
    dairy_cuttings : int
        Initial number of dairy hay cuttings (the default is 5).
    overwrite_flag : bool
        If True, overwrite existing files (the default is False).

    Returns
    -------
    None

    """
    logging.info('\nBuilding ET-Demands Static Files')

    # Default values
    permeability = -999
    soil_depth = 60  # inches
    aridity = 50
    irrigation = 1
    # DEADBEEF - The number of crops should not be hardcoded here
    crops = 123

    # Input paths
    # DEADBEEF - For now, get cropET folder from INI file
    # This function may eventually be moved into the main cropET code
    config = copy.deepcopy(cfg_prep)

    try:
        project_ws = config.CROP_ET.project_folder
    except:
        logging.error('project_folder parameter must be set in the INI file, exiting')
        return False
    try:
        gis_ws = config.CROP_ET.gis_folder
    except:
        logging.error('gis_folder parameter must be set in the INI file, exiting')
        return False
    try:
        et_cells_path = config.CROP_ET.cells_path
    except:
        logging.error('cells_path parameter must be set in the INI file, exiting')
        return False
    try:
        crop_et_ws = config.CROP_ET.crop_et_folder
    except:
        logging.error('crop_et_folder parameter must be set in the INI file, exiting')
        return False
    try:
        template_ws = config.CROP_ET.template_folder
    except:
        logging.error('CROP_ET template_folder parameter must be set in the INI file, exiting')
        return False

    # Read data from geodatabase or shapefile
    # if '.gdb' in et_cells_path and not et_cells_path.endswith('.shp'):
    #     _flag = False
    #     _path = os.path.dirname(et_cells_path)
    #      gdb_path = r'D:\Projects\CAT_Basins\AltusOK\et-demands_py\et_demands.gdb'
    #     _cells_path = os.path.join(gdb_path, 'et_cells')

    # Output sub-folder names
    static_ws = os.path.join(project_ws, 'static')

    # basin attributes fields
    basin_id_filed = 'STAID'
    basin_elev_field = 'ELEV_MEAN_M_BASIN'

    # ET Cell field names
    cell_lat_field = 'LAT'
    cell_lon_field = 'LON'
    cell_id_field = 'GAGE_ID'
    # cell_station_id_field = 'STATION_ID'
    # awc_field = 'AWC'
    clay_field = 'CLAY'
    sand_field = 'SAND'
    awc_in_ft_field = 'AWC_IN_FT'
    hydgrp_num_field = 'HYDGRP_NUM'
    hydgrp_field = 'HYDGRP'

    # huc_field = 'HUC{}'.format(huc)
    # permeability_field = 'PERMEABILITY'
    # soil_depth_field = 'SOIL_DEPTH'
    # aridity_field = 'ARIDITY'
    # dairy_cutting_field = 'DAIRY_CUTTINGS'
    # beef_cutting_field = 'BEEF_CUTTINGS'

    # Static file names
    cell_props_name = 'ETCellsProperties.txt'
    cell_crops_name = 'ETCellsCrops.txt'
    cell_cuttings_name = 'MeanCuttings.txt'
    crop_params_name = 'CropParams.txt'
    crop_coefs_name = 'CropCoefs.txt'
    crop_coefs_eto = 'CropCoefs_eto.txt'
    crop_coefs_etr = 'CropCoefs_etr.txt'
    eto_ratio_name = 'EToRatiosMon.txt'
    etr_ratio_name = 'ETrRatiosMon.txt'
    static_list = [crop_params_name, crop_coefs_name, crop_coefs_eto,
                   crop_coefs_etr, cell_props_name, cell_crops_name,
                   cell_cuttings_name, eto_ratio_name, etr_ratio_name]

    # Check input folders
    if not os.path.isdir(crop_et_ws):
        logging.critical('\nERROR: The INI cropET folder does not exist'
                         '\n  {}'.format(crop_et_ws))
        sys.exit()
    elif not os.path.isdir(project_ws):
        logging.critical('\nERROR: The project folder does not exist'
                         '\n  {}'.format(project_ws))
        sys.exit()
    elif not os.path.isdir(gis_ws):
        logging.critical('\nERROR: The GIS folder does not exist'
                         '\n  {}'.format(gis_ws))
        sys.exit()
    logging.info('\nGIS Workspace:      {}'.format(gis_ws))
    logging.info('Project Workspace:  {}'.format(project_ws))
    logging.info('CropET Workspace:   {}'.format(crop_et_ws))
    logging.info('Template Workspace: {}'.format(template_ws))

    # Check input files
    if not _arcpy.exists(et_cells_path):
        logging.critical('\nERROR: The ET Cell shapefile does not exist'
                         '\n  {}'.format(et_cells_path))
        sys.exit()
    for static_name in static_list:
        if not os.path.isfile(os.path.join(template_ws, static_name)):
            logging.error(
                '\nERROR: The static template does not exist'
                '\n  {}'.format(os.path.join(template_ws, static_name)))
            sys.exit()
    logging.debug('ET Cells Path: {}'.format(et_cells_path))

    # Build output table folder if necessary
    if not os.path.isdir(static_ws):
        os.makedirs(static_ws)

    # Read ET Cell zonal stats
    logging.info('\nReading ET Cell Zonal Stats')
    logging.debug('  {}'.format(et_cells_path))
    crop_field_list = sorted([f for f in _arcpy.list_fields(et_cells_path) if re.match('CROP_\d{3}', f)])
    fields = [cell_id_field, cell_lat_field, cell_lon_field, awc_in_ft_field, clay_field, sand_field, hydgrp_num_field,
              hydgrp_field]
    fields = fields + crop_field_list
    logging.debug('  Fields: {}'.format(fields))
    cell_data_dict = defaultdict(dict)

    for fid, row in _arcpy.search_cursor(et_cells_path, fields).items():
        # Switch to cell_id_field as index (instead of FID)
        for f in fields[1:]:
            cell_data_dict[str(row[cell_id_field])][f] = row[f]

    # Read basin data
    logging.info('\nReading basin attributes')
    fields = [basin_elev_field]
    logging.debug('  Fields: {}'.format(fields))
    basin_data_dict = defaultdict(dict)
    basin_topo = pd.read_csv(config.GAGES.basin_topo_file, sep=',', dtype={0: str})
    for cell_id_tmp in list(cell_data_dict.keys()):
        basin_data_dict[cell_id_tmp][basin_elev_field] = basin_topo.loc[
            basin_topo[basin_id_filed] == cell_id_tmp, basin_elev_field].values[0]
    # Convert elevation units if necessary
    # logging.debug('  Convert station elevation from meters to feet')
    # for k in basin_data_dict.keys():
    #     basin_data_dict[k][basin_elev_field] /= 0.3048

    # static files
    logging.info('\nCopying template static files')
    for static_name in static_list:
        # if (overwrite_flag or
        #         os.path.isfile(os.path.join(static_ws, static_name))):
        logging.debug('  {}'.format(static_name))
        shutil.copy(os.path.join(template_ws, static_name), static_ws)
        # shutil.copyfile(
        #     .path.join(template_ws, static_name),
        #     .path.join(static_ws, crop_params_name))

    logging.info('\nWriting static text files')
    cell_props_path = os.path.join(static_ws, cell_props_name)
    cell_crops_path = os.path.join(static_ws, cell_crops_name)
    cell_cuttings_path = os.path.join(static_ws, cell_cuttings_name)
    # crop_params_path = os.path.join(static_ws, crop_params_name)
    # crop_coefs_path = os.path.join(static_ws, crop_coefs_name)
    eto_ratio_path = os.path.join(static_ws, eto_ratio_name)
    etr_ratio_path = os.path.join(static_ws, etr_ratio_name)

    # Write cell properties
    logging.debug('  {}'.format(cell_props_path))
    with open(cell_props_path, 'a') as output_f:
        for cell_id, cell_data in sorted(cell_data_dict.items()):
            basin_id = cell_id
            basin_lat = '{:>9.4f}'.format(cell_data[cell_lat_field])
            basin_lon = '{:>9.4f}'.format(cell_data[cell_lon_field])
            basin_data = basin_data_dict[basin_id]
            basin_elev = '{:.2f}'.format(basin_data[basin_elev_field])
            # There is an extra/unused column in the template and excel files
            output_list = [cell_id, cell_id, basin_id, basin_lat, basin_lon, basin_elev, permeability,
                           '{:.4f}'.format(cell_data[awc_in_ft_field]), soil_depth, cell_data[hydgrp_field],
                           cell_data[hydgrp_num_field], aridity, '']
            output_f.write('\t'.join(map(str, output_list)) + '\n')

            del output_list
            del basin_id, basin_lat, basin_lon, basin_elev

    # Write cell crops
    logging.debug('  {}'.format(cell_crops_path))
    with open(cell_crops_path, 'a') as output_f:
        for cell_id, cell_data in sorted(cell_data_dict.items()):
            basin_id = cell_id
            output_list = [cell_id, cell_id, basin_id, irrigation]
            crop_list = ['CROP_{:03d}'.format(i) for i in range(1, crops + 1)]
            crop_area_list = []
            for crop in crop_list:
                if crop in cell_data.keys() and cell_data[crop] is not None:
                    crop_area_list.append(cell_data[crop])
                else:
                    crop_area_list.append(0)
            crop_flag_list = [1 if area > area_threshold else 0 for area in crop_area_list]
            output_list = output_list + crop_flag_list
            output_f.write('\t'.join(map(str, output_list)) + '\n')

            del crop_list, crop_area_list, crop_flag_list, output_list

    # Write cell cuttings
    logging.debug('  {}'.format(cell_cuttings_path))
    with open(cell_cuttings_path, 'a') as output_f:
        for cell_id, cell_data in sorted(cell_data_dict.items()):
            output_list = [cell_id, cell_id, '{:>9.4f}'.format(cell_data[cell_lat_field]), dairy_cuttings,
                           beef_cuttings]
            output_f.write('\t'.join(map(str, output_list)) + '\n')

    # Write monthly ETo ratios
    logging.debug('  {}'.format(eto_ratio_path))
    with open(eto_ratio_path, 'a') as output_f:
        for cell_id, cell_data in sorted(cell_data_dict.items()):
            basin_id = cell_id
            output_f.write('\t'.join(map(str, [basin_id, ''] + [1.0] * 12)) + '\n')

    # Write monthly ETr ratios
    logging.debug('  {}'.format(etr_ratio_path))
    with open(etr_ratio_path, 'a') as output_f:
        for cell_id, cell_data in sorted(cell_data_dict.items()):
            basin_id = cell_id
            output_f.write('\t'.join(map(str, [basin_id, ''] + [1.0] * 12)) + '\n')


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='ET-Demands Static Files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--acres', default=0.25, type=float, help='Crop area threshold')
    parser.add_argument('--beef', default=4, type=int, help='Number of beef hay cuttings')
    parser.add_argument('--dairy', default=5, type=int, help='Number of dairy hay cuttings')
    parser.add_argument('-o', '--overwrite', default=None, action='store_true', help='Overwrite existing file')
    parser.add_argument('--debug', default=logging.INFO, const=logging.DEBUG, help='Debug level logging',
                        action="store_const", dest="loglevel")
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    logging.info('{0:<20s} {1}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{0:<20s} {1}'.format('Current Directory:', os.getcwd()))
    logging.info('{0:<20s} {1}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(area_threshold=args.acres,
         dairy_cuttings=args.dairy, beef_cuttings=args.beef,
         overwrite_flag=args.overwrite)
