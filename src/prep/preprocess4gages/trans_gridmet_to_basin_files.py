import fnmatch
import os
import shutil

import pandas as pd
import numpy as np
from src.config.config_prep import cfg_prep
import geopandas as gpd


def choose_some_gauge():
    shpfile = cfg_prep.CROP_ET.cells_path
    shape_data = gpd.read_file(shpfile)
    shape_data_sort = shape_data.sort_values(by="GAGE_ID")
    gages_id = shape_data_sort['GAGE_ID'].values

    data_dir = cfg_prep.GRIDMET.origin_gridmet_folder
    output_dir = cfg_prep.CROP_ET.refet_folder
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    gage_id_file = cfg_prep.GAGES.gage_id_file
    data_all = pd.read_csv(gage_id_file, sep=',', dtype={0: str})
    gage_fld_lst = data_all.columns.values
    df_id_region = data_all.iloc[:, 0].values
    xy, ind1, ind2 = np.intersect1d(df_id_region, gages_id, return_indices=True)
    assert xy.size == len(gages_id)
    data = data_all.iloc[ind1, :]
    gage_dict = dict()
    for s in gage_fld_lst:
        if s is gage_fld_lst[1]:
            gage_dict[s] = data[s].values.tolist()
        else:
            gage_dict[s] = data[s].values
    for j in range(len(gages_id)):
        huc_id = gage_dict['HUC02'][j]
        data_huc_dir = os.path.join(data_dir, huc_id)
        src = os.path.join(data_huc_dir, gage_dict['STAID'][j] + '_lump_gridmet_forcing.txt')
        dst = os.path.join(output_dir, 'gridmet_historical_%s.txt' % (gage_dict['STAID'][j]))
        print("write into", dst)
        shutil.copy(src, dst)


def trans_all_forcing_file_to_camels(t_range):
    """the function need to be run region by region"""
    output_dir = cfg_prep.GRIDMET.origin_gridmet_folder
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    region_name = "MxWdShld"  # cfg_prep.CROP_ET.region_name.split("_")[-1]
    # forcing data file generated is named as "allref", so rename the "all"
    if region_name == "all":
        region_name = "allref"

    if region_name == "allref":
        shapefile = os.path.join(cfg_prep.GAGES.gage_region_dir, 'bas_ref_all.shp')
    else:
        shapefile = os.path.join(cfg_prep.GAGES.gage_region_dir, 'bas_nonref_' + region_name + '.shp')
    shape_data = gpd.read_file(shapefile)
    shape_data_sort = shape_data.sort_values(by="GAGE_ID")
    gages_id = shape_data_sort['GAGE_ID'].values

    gage_id_file = cfg_prep.GAGES.gage_id_file
    data_all = pd.read_csv(gage_id_file, sep=',', dtype={0: str})
    gage_fld_lst = data_all.columns.values
    df_id_region = data_all.iloc[:, 0].values
    c, ind1, ind2 = np.intersect1d(df_id_region, gages_id, return_indices=True)
    data = data_all.iloc[ind1, :]
    gage_dict = dict()
    for s in gage_fld_lst:
        if s is gage_fld_lst[1]:
            gage_dict[s] = data[s].values.tolist()
        else:
            gage_dict[s] = data[s].values

    year_start = int(t_range[0].split("-")[0])
    year_end = int(t_range[1].split("-")[0])
    years = np.arange(year_start, year_end)
    assert (all(x < y for x, y in zip(gages_id, gages_id[1:])))
    for year in years:
        trans_gridmet_to_basins_files(output_dir, output_dir, gage_dict, region_name, year)


def trans_gridmet_to_basins_files(daymet_dir, output_dir, gage_dict, region, year):
    """transform forcing data of gridmet formats to the one in camels dataset"""
    # don't change!
    name_dataset = ['gage_id', "time_start", "pr", "rmax", "rmin", "sph", "srad", "th", "tmmn", 'tmmx', 'vs', 'erc',
                    'eto', 'bi', 'fm100', 'fm1000', 'etr', 'vpd']
    camels_index = ['Year', 'Mnth', 'Day', 'Hr', "pr", "rmax", "rmin", "sph", "srad", "th", "tmmn", 'tmmx', 'vs', 'erc',
                    'eto', 'bi', 'fm100', 'fm1000', 'etr', 'vpd']
    for f_name in os.listdir(daymet_dir):
        if fnmatch.fnmatch(f_name, 'gridmet_' + region + '_mean_' + str(year) + '.csv'):
            data_file = os.path.join(daymet_dir, f_name)
            data_temp = pd.read_csv(data_file, sep=',', dtype={name_dataset[0]: str})
            for i_basin in range(gage_dict['STAID'].size):
                # name csv
                basin_data = data_temp[data_temp[name_dataset[0]] == gage_dict['STAID'][i_basin]]
                # get Year,Month,Day,Hour info
                csv_date = pd.to_datetime(basin_data[name_dataset[1]])
                year_month_day_hour = pd.DataFrame([[dt.year, dt.month, dt.day, dt.hour] for dt in csv_date],
                                                   columns=camels_index[0:4])
                data_df = pd.DataFrame(basin_data.iloc[:, 2:].values, columns=camels_index[4:])
                # concat
                new_data_df = pd.concat([year_month_day_hour, data_df], axis=1)
                # output the result
                huc_id = gage_dict['HUC02'][i_basin]
                output_huc_dir = os.path.join(output_dir, huc_id)
                if not os.path.isdir(output_huc_dir):
                    os.mkdir(output_huc_dir)
                output_file = os.path.join(output_huc_dir, gage_dict['STAID'][i_basin] + '_lump_gridmet_forcing.txt')
                print("output forcing data of", gage_dict['STAID'][i_basin], "year", str(year))
                if os.path.isfile(output_file):
                    data_old = pd.read_csv(output_file, sep=' ')
                    years = np.unique(data_old[camels_index[0]].values)
                    if year in years:
                        continue
                    else:
                        os.remove(output_file)
                        new_data_df = pd.concat([data_old, new_data_df]).sort_values(by=camels_index[0:3])
                new_data_df.to_csv(output_file, header=True, index=False, sep=' ', float_format='%.2f')


if __name__ == "__main__":
    t_range = ["2008-01-01", "2009-01-01"]
    # trans_all_forcing_file_to_camels(t_range)
    choose_some_gauge()
