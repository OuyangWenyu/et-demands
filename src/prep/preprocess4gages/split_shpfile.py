"""split a shapefile to multiple ones"""
import copy
import os
import geopandas as gpd
from src.config.config_prep import cfg_prep

config = copy.deepcopy(cfg_prep)
fp = config.CROP_ET.cells_path
shp_folder = config.CROP_ET.cells_path
if not os.path.isdir(shp_folder):
    os.makedirs(shp_folder)
# Print out the full file path
print(fp)

# Read file using gpd.read_file()
data = gpd.read_file(fp)

print(type(data))
# 注意观察，geometry是一个由一系列坐标点组成的list，放入polygon的
print(data.head())
print(data.columns)
print(data.crs)

# 索引和dataframe一致
for i in range(2):
    print('第' + str(i) + "个", data.iloc[i, :], '\n')
    output_fp = os.path.join(shp_folder, str(data.iloc[i, :]['GAGE_ID']) + ".shp")
    if os.path.isfile(output_fp):
        continue
    newdata = gpd.GeoDataFrame()
    # 要赋值到0位置上，否则就成为geoseries了
    newdata.at[0, 'geometry'] = data.iloc[i, :]['geometry']
    print(type(newdata.at[0, 'geometry']))
    newdata.at[0, 'AREA'] = data.iloc[i, :]['AREA']
    newdata.at[0, 'PERIMETER'] = data.iloc[i, :]['PERIMETER']
    newdata.at[0, 'GAGE_ID'] = data.iloc[i, :]['GAGE_ID']
    # Set the GeoDataFrame's coordinate system to WGS84 (i.e. epsg code 4326)
    newdata.crs = data.crs
    newdata.to_file(output_fp)
