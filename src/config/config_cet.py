import copy
import os

from easydict import EasyDict as edict

import definition

__CET = edict()
cfg_cet = __CET

# Project directory
__CET.CODE_ROOT_DIR = os.path.join(definition.ROOT_DIR, "src")
__CET.DATA_ROOT_DIR = os.path.join(definition.ROOT_DIR, "examples")

# RefET data (ETo or ETr)
__CET.REFET = edict()
__CET.REFET.refet_type = "ETo"
__CET.REFET.refet_folder = "climate"
__CET.REFET.name_format = "gridmet_historical_%s.txt"
__CET.REFET.header_lines = 1
# 1's based indices
__CET.REFET.names_line = 1
__CET.REFET.delimiter = " "
# Field names and units
# __CET.REFET.date_field = "date"
__CET.REFET.year_field = "Year"
__CET.REFET.month_field = "Mnth"
__CET.REFET.day_field = "Day"
__CET.REFET.etref_field = "eto"
__CET.REFET.etref_units = "mm/day"

# Weather data (Tmin, Tmax, PPT, etc.)
__CET.WEATHER = edict()
__CET.WEATHER.weather_folder = "climate"
__CET.WEATHER.name_format = "gridmet_historical_%s.txt"
__CET.WEATHER.header_lines = 1
# 1's based indices
__CET.WEATHER.names_line = 1
__CET.WEATHER.delimiter = " "
# Field names
# __CET.WEATHER.date_field = "date"
__CET.WEATHER.year_field = "Year"
__CET.WEATHER.month_field = "Mnth"
__CET.WEATHER.day_field = "Day"
__CET.WEATHER.tmin_field = "tmmn"
__CET.WEATHER.tmax_field = "tmmx"
__CET.WEATHER.ppt_field = "pr"
__CET.WEATHER.rs_field = "srad"
__CET.WEATHER.wind_field = "vs"
__CET.WEATHER.rh_min_field = "rmin"
# Units
__CET.WEATHER.tmin_units = "K"
__CET.WEATHER.tmax_units = "K"
__CET.WEATHER.ppt_units = "mm"
__CET.WEATHER.rs_units = "W/m2"
__CET.WEATHER.wind_units = "m/s"
__CET.WEATHER.rh_min_units = "%"
# Wind height in meters
__CET.WEATHER.wind_height = 10


def crop_et_config(old_config, region_name):
    new_config = copy.deepcopy(old_config)
    # ET Demands Example Input File
    new_config.CROP_ET = edict()
    new_config.CROP_ET.basin_id = "GAGES-II basins"
    new_config.CROP_ET.region_name = region_name
    new_config.CROP_ET.project_folder = os.path.join(new_config.DATA_ROOT_DIR, new_config.CROP_ET.region_name)
    new_config.CROP_ET.gis_folder = os.path.join(new_config.CROP_ET.project_folder, 'gis')
    new_config.CROP_ET.region_shpfile_dir = os.path.join(new_config.DATA_ROOT_DIR, new_config.CROP_ET.region_name)
    new_config.CROP_ET.cells_path = os.path.join(new_config.CROP_ET.region_shpfile_dir,
                                                 new_config.CROP_ET.region_name + '.shp')

    # ET-Demands folder
    new_config.CROP_ET.crop_et_folder = os.path.join(new_config.CODE_ROOT_DIR, "cropet4gages")
    new_config.CROP_ET.template_folder = os.path.join(new_config.CODE_ROOT_DIR, "static")

    # Crops
    # crop_test_list = 66
    # crop_skip_list = 4-57
    # cell_test_list = 384315
    # cell_test_list = [377392, 378777, 378778, 380159, 380160, 380161, 380163, 380164, 384315, 395415, 400971, 406506, 409254, 416106, 514602, 549203, 583875, 527057, 524331 514572, 510402, 504862]
    # Stats flags
    new_config.CROP_ET.daily_stats_flag = True
    new_config.CROP_ET.monthly_stats_flag = True
    new_config.CROP_ET.annual_stats_flag = True
    new_config.CROP_ET.growing_season_stats_flag = True

    # Spatially varying calibration
    new_config.CROP_ET.spatial_cal_flag = False
    new_config.CROP_ET.spatial_cal_folder = os.path.join(new_config.CROP_ET.project_folder, "calibration")

    # Output alfalfa cuttings
    new_config.CROP_ET.cutting_flag = True
    # Output net-irrigation water requirement (NIWR)
    new_config.CROP_ET.niwr_flag = True
    # Output crop coefficient (Kc)
    new_config.CROP_ET.kc_flag = True

    # Limit to a date range (ISO Format: YYYY-MM-DD)
    new_config.CROP_ET.start_date = None
    new_config.CROP_ET.end_date = None

    # Sub folder names
    new_config.CROP_ET.static_folder = "static"
    new_config.CROP_ET.daily_output_folder = "daily_stats"
    new_config.CROP_ET.monthly_output_folder = "monthly_stats"
    new_config.CROP_ET.annual_output_folder = "annual_stats"
    new_config.CROP_ET.gs_output_folder = "growing_season_stats"

    # Plots sub-folder names
    new_config.CROP_ET.daily_plots_folder = "daily_plots"

    # Static file names
    new_config.CROP_ET.cell_properties_name = "ETCellsProperties.txt"
    new_config.CROP_ET.cell_crops_name = "ETCellsCrops.txt"
    new_config.CROP_ET.cell_cuttings_name = "MeanCuttings.txt"
    new_config.CROP_ET.crop_params_name = "CropParams.txt"
    new_config.CROP_ET.crop_coefs_name = "fao56-table12.csv"
    new_config.CROP_ET.crop_coefs_path = os.path.join(new_config.CODE_ROOT_DIR, "prep", "preprocess4gages",
                                                      "fao56_cropcoefs_eto.csv")
    new_config.CROP_ET.et_ratios_name = "ETrRatiosMon.txt"
    new_config.CROP_ET.cdl_crop_class_path = os.path.join(new_config.CODE_ROOT_DIR, "prep", "preprocess4gages",
                                                          "cdl_crop_class.csv")
    new_config.CROP_ET.cdl_crosswalk_fao56_etd_path = os.path.join(new_config.CODE_ROOT_DIR, "prep", "preprocess4gages",
                                                                   "cdl_crosswalk_fao56_etd.csv")
    new_config.CROP_ET.crop_key_points_file = os.path.join(new_config.CODE_ROOT_DIR, "prep", "preprocess4gages",
                                                           "etd_crop_stage_points.csv")

    # Misc
    new_config.CROP_ET.elev_units = "Feet"
    return new_config
