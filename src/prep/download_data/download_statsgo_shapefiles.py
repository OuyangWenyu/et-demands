# --------------------------------
# Name:         download_soils.py
# Purpose:      Download AWC, clay and sand shapefiles
# --------------------------------

import argparse
import copy
import datetime as dt
import logging
import os
import sys

import src.prep._util as util
from src.config.config_prep import cfg_prep


def main(overwrite_flag=False):
    """Download soil available water capacity (AWC), clay and sand shapefiles

    Parameters
    ----------
    overwrite_flag : bool, optional
        If True, overwrite existing files (the default is False).

    Returns
    -------
    None

    Notes
    -----
    Only the STATSGO 0to152cm shapefiles are currently available in the bucket.
    Other products, depths, or SSURGO shapefiles may eventually be available.
    
    """
    logging.info('\nDownload soil shapefiles')

    config = copy.deepcopy(cfg_prep)

    base_url = 'https://storage.googleapis.com/openet/statsgo/shapefiles'
    ext_list = ['.shp', '.dbf', '.prj', '.shx', '.sbn', '.sbx']

    awc_name = 'AWC_WTA_0to152cm_statsgo.shp'
    clay_name = 'Clay_WTA_0to152cm_statsgo.shp'
    sand_name = 'Sand_WTA_0to152cm_statsgo.shp'

    awc_url = '{}/{}'.format(base_url, awc_name)
    clay_url = '{}/{}'.format(base_url, clay_name)
    sand_url = '{}/{}'.format(base_url, sand_name)

    awc_path = config.SOILS.awc_path
    clay_path = config.SOILS.clay_path
    sand_path = config.SOILS.sand_path

    if not os.path.isdir(os.path.dirname(awc_path)):
        os.makedirs(os.path.dirname(awc_path))
    if not os.path.isdir(os.path.dirname(clay_path)):
        os.makedirs(os.path.dirname(clay_path))
    if not os.path.isdir(os.path.dirname(sand_path)):
        os.makedirs(os.path.dirname(sand_path))

    if not os.path.isfile(awc_path) or overwrite_flag:
        logging.info('\nDownloading AWC shapefile')
        for ext in ext_list:
            logging.debug('  {}'.format(awc_url.replace('.shp', ext)))
            logging.debug('  {}'.format(awc_path.replace('.shp', ext)))
            util.url_download(awc_url.replace('.shp', ext),
                              awc_path.replace('.shp', ext))
    else:
        logging.info('\nAWC shapefile already downloaded')

    if not os.path.isfile(clay_path) or overwrite_flag:
        logging.info('\nDownloading Clay shapefile')
        for ext in ext_list:
            logging.debug('  {}'.format(clay_url.replace('.shp', ext)))
            logging.debug('  {}'.format(clay_path.replace('.shp', ext)))
            util.url_download(clay_url.replace('.shp', ext),
                              clay_path.replace('.shp', ext))
    else:
        logging.info('\nClay shapefile already downloaded')

    if not os.path.isfile(sand_path) or overwrite_flag:
        logging.info('\nDownloading Sand shapefile')
        for ext in ext_list:
            logging.debug('  {}'.format(sand_url.replace('.shp', ext)))
            logging.debug('  {}'.format(sand_path.replace('.shp', ext)))
            util.url_download(sand_url.replace('.shp', ext),
                              sand_path.replace('.shp', ext))
    else:
        logging.info('\nSand shapefile already downloaded')


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Download Soils Shapefiles',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-o', '--overwrite', default=None, action="store_true",
        help='Force overwrite of existing files')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    log_f = '{:<20s} {}'
    logging.info(log_f.format('Start Time:', dt.datetime.now().isoformat(' ')))
    logging.info(log_f.format('Current Directory:', os.getcwd()))
    logging.info(log_f.format('Script:', os.path.basename(sys.argv[0])))

    main(overwrite_flag=args.overwrite)
