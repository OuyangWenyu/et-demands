"""split a shapefile to multiple ones or """
import json
import logging
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from src.config.config_prep import cfg_prep


def split_shpfile(chosen_ids, shp_folder, write_flag=False):
    gage_classif_file = cfg_prep.GAGES.basin_classif_file
    data_all = pd.read_csv(gage_classif_file, sep=',', dtype={0: str}, usecols=range(0, 3))
    all_sites_id = data_all.iloc[:, 0].values
    assert (all(x < y for x, y in zip(all_sites_id, all_sites_id[1:])))
    all_regions = data_all[data_all['STAID'].isin(sites_id)]['AGGECOREGION']
    all_isref = data_all[data_all['STAID'].isin(sites_id)]['CLASS']
    region_lst = np.unique(
        ["bas_ref_all" if y == 'Ref' else "bas_" + "".join(y.split("-")).lower() + "_" + x for x, y in
         zip(all_regions.values, all_isref.values)])
    fp_lst = [os.path.join(cfg_prep.GAGES.gage_region_dir, region_tmp + ".shp") for region_tmp in region_lst]
    gdf_lst = []
    # Read file using gpd.read_file()
    for fp in fp_lst:
        data_origin = gpd.read_file(fp)
        data = data_origin.sort_values(by="GAGE_ID")
        logging.debug(type(data))
        # 注意观察，geometry是一个由一系列坐标点组成的list，放入polygon的
        logging.debug(data.head())
        logging.debug(data.columns)
        logging.debug(data.crs)

        sites_this_region, ind1, ind2 = np.intersect1d(data["GAGE_ID"].values, chosen_ids, return_indices=True)

        # 索引和dataframe一致
        for i in ind1:
            output_fp = os.path.join(shp_folder, str(data.iloc[i, :]['GAGE_ID']) + ".shp")
            if os.path.isfile(output_fp):
                continue
            newdata = gpd.GeoDataFrame()
            # 要赋值到0位置上，否则就成为geoseries了
            newdata.at[0, 'geometry'] = data.iloc[i, :]['geometry']
            logging.debug(type(newdata.at[0, 'geometry']))
            # trans m^2 to km^2 to ensure no too larger number
            # newdata.at[0, 'AREA'] = data.iloc[i, :]['AREA'] / 1000000
            # newdata.at[0, 'PERIMETER'] = data.iloc[i, :]['PERIMETER']
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
        gdf_origin = gpd.GeoDataFrame(pd.concat(gdf_lst_input))
        gdf = gdf_origin.sort_values(by='GAGE_ID')
        gdf.crs = gdf_lst_input[0].crs
        if write_flag:
            gdf.to_file(output_shpfile)


if __name__ == '__main__':
    # region_name = "some_from_irrigation"
    region_name = "some_from_3557"
    # sites_id = ["01013500", "01017000", "05592575"]
    # sites_id = pd.read_csv("irrigation_gage_id.csv", dtype={0: str}).sort_values(by="GAGE_ID")[
    #     "GAGE_ID"].values.tolist()
    with open("dictTimeSpace.json", 'r') as fp:
        all_sites_json = json.load(fp)
    sites_id = all_sites_json["sites_id"]
    output_folder = os.path.join(cfg_prep.DATA_ROOT_DIR, region_name)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    gdf_lst = split_shpfile(sites_id, output_folder)
    output_fp = os.path.join(output_folder, region_name + ".shp")
    merge_shpfile(gdf_lst, output_fp)
