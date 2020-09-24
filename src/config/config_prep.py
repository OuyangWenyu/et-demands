import os

from easydict import EasyDict as edict

import definition

__C = edict()
cfg_prep = __C
# Project directory
__C.CODE_ROOT_DIR = os.path.join(definition.ROOT_DIR, "src")
__C.DATA_ROOT_DIR = os.path.join(definition.ROOT_DIR, "examples", "gages")

# USDA CDL directory
__C.USDA = edict()
__C.USDA.cdl_folder = os.path.join(__C.DATA_ROOT_DIR, 'gis', "usda")
__C.USDA.cdl_year = 2008
__C.USDA.cdl_format = "{}_30m_cdls.{}"
__C.USDA.usda_site_url = 'ftp.nass.usda.gov'
__C.USDA.usda_site_folder = 'download/res'
# Crop 61 is fallow/idle and was excluded from analysis
# Crop 176 is Grassland/Pasture in the new national CDL rasters
# Crop 181 was Pasture/Hay in the old state CDL rasters
# Crop 182 was Cultivated Crop in the old state CDL rasters
__C.USDA.cdl_crops = "1-60, 66-80, 97-100, 204-254"
# cdl_nonag = "61-65, 81-96, 101-203, 255"

# GAGES
__C.GAGES = edict()
__C.GAGES.attrUrl = ["https://water.usgs.gov/GIS/dsdl/basinchar_and_report_sept_2011.zip",
                     "https://water.usgs.gov/GIS/dsdl/gagesII_9322_point_shapefile.zip",
                     "https://water.usgs.gov/GIS/dsdl/boundaries_shapefiles_by_aggeco.zip",
                     "https://www.sciencebase.gov/catalog/file/get/59692a64e4b0d1f9f05fbd39"]
# region shapefiles
__C.GAGES.GAGES_PATH = os.path.join(__C.DATA_ROOT_DIR, 'gis', "gagesii")
__C.GAGES.gage_region_dir = os.path.join(__C.GAGES.GAGES_PATH, 'boundaries_shapefiles_by_aggeco',
                                         'boundaries-shapefiles-by-aggeco')
# point shapefile
__C.GAGES.gagesii_points_dir = os.path.join(__C.GAGES.GAGES_PATH, "gagesII_9322_point_shapefile")
__C.GAGES.gagesii_points_file = os.path.join(__C.GAGES.gagesii_points_dir, "gagesII_9322_sept30_2011.shp")
# all USGS sites
__C.GAGES.attrDir = os.path.join(__C.GAGES.GAGES_PATH, "basinchar_and_report_sept_2011")
__C.GAGES.gage_files_dir = os.path.join(__C.GAGES.attrDir, 'spreadsheets-in-csv-format')
__C.GAGES.gage_id_file = os.path.join(__C.GAGES.gage_files_dir, 'conterm_basinid.txt')

# NOAA RefET
__C.NOAA = edict()
__C.NOAA.noaa_site_url = 'ftp2.psl.noaa.gov'
__C.NOAA.noaa_site_folder = 'Projects/RefET/CONUS/Gen-0/data'
__C.NOAA.noaa_year = 2008
__C.NOAA.noaa_folder = os.path.join(__C.DATA_ROOT_DIR, 'climate', "noaa_daily_ret")

# CROP ET setting
__C.CROP_ET = edict()
__C.CROP_ET.project_folder = __C.DATA_ROOT_DIR
__C.CROP_ET.gis_folder = os.path.join(__C.DATA_ROOT_DIR, 'gis')
__C.CROP_ET.crop_path = os.path.join(__C.CROP_ET.gis_folder, 'cdl')
__C.CROP_ET.awc_path = os.path.join(__C.CROP_ET.gis_folder, 'soils', 'AWC_WTA_0to152cm_statsgo.shp')
__C.CROP_ET.clay_path = os.path.join(__C.CROP_ET.gis_folder, 'soils', 'Clay_WTA_0to152cm_statsgo.shp')
__C.CROP_ET.sand_path = os.path.join(__C.CROP_ET.gis_folder, 'soils', 'Sand_WTA_0to152cm_statsgo.shp')

__C.CROP_ET.cells_path = os.path.join(__C.GAGES.gage_region_dir, 'bas_nonref_MxWdShld.shp')
# stations_path = os.path.join(definition.ROOT_DIR,"testing","data","gis","stations","gridmet_huc8_stations.shp")
__C.CROP_ET.crop_field = "CDL"
