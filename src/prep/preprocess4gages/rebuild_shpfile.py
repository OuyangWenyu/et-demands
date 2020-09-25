"""split a shapefile to multiple ones or """
import copy
import os
import pandas as pd
import geopandas as gpd
from src.config.config_prep import cfg_prep


def split_shpfile(fp, shp_folder, write_flag=False):
    # Read file using gpd.read_file()
    data = gpd.read_file(fp)

    print(type(data))
    # 注意观察，geometry是一个由一系列坐标点组成的list，放入polygon的
    print(data.head())
    print(data.columns)
    print(data.crs)

    gdf_lst = []
    # 索引和dataframe一致
    for i in range(10):
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
        if write_flag:
            newdata.to_file(output_fp)
        gdf_lst.append(newdata)
    return gdf_lst


def merge_shpfile(gdf_lst_input, output_shpfile, write_flag=True):
    if os.path.isfile(output_shpfile):
        print("already done!")
    else:
        gdf = gpd.GeoDataFrame(pd.concat(gdf_lst_input))
        gdf.crs = gdf_lst_input[0].crs
        if write_flag:
            gdf.to_file(output_shpfile)


if __name__ == '__main__':
    config = copy.deepcopy(cfg_prep)
    input_shpfile = os.path.join(config.GAGES.gage_region_dir, 'bas_nonref_MxWdShld.shp')
    region_name = "some_from_mxwdshld"
    output_folder = os.path.join(config.DATA_ROOT_DIR, region_name)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    gdf_lst = split_shpfile(input_shpfile, output_folder)
    output_fp = os.path.join(output_folder, region_name + ".shp")
    merge_shpfile(gdf_lst, output_fp)
