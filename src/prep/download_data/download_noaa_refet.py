# --------------------------------
# Name:         download_noaa_refet.py
# Purpose:      Download NOAA RefET zips
# --------------------------------

import argparse
import datetime as dt
import logging
import os
import sys

from src.prep import _util as util
from src.config.config_prep import cfg_prep


def main(overwrite_flag=False):
    """Download CONUS NOAA RefET zips

    Parameters
    ----------
    overwrite_flag : bool
        If True, overwrite existing files (the default is False).

    Returns
    -------
    None

    """
    logging.info('\nDownload and extract CONUS NOAA RefET files')

    noaa_ws = cfg_prep.NOAA.noaa_folder
    noaa_year = cfg_prep.NOAA.noaa_year

    site_url = cfg_prep.NOAA.noaa_site_url
    site_folder = cfg_prep.NOAA.noaa_site_folder + '/' + str(noaa_year)

    logging.info('Year: {}'.format(noaa_year))
    one_year_url = site_url + '/' + site_folder
    noaa_path = os.path.join(noaa_ws, str(noaa_year))

    size_flag = False

    if not os.path.isdir(noaa_path):
        os.makedirs(noaa_path)

    if os.path.isdir(noaa_path) and (overwrite_flag or size_flag):
        os.remove(noaa_path)

    if not os.path.isdir(noaa_path):
        logging.info('  Download NOAA RefET files')
        logging.debug(one_year_url)
        logging.debug(noaa_path)

        util.ftp_download_dir(site_url, site_folder, noaa_path)


def arg_parse():
    parser = argparse.ArgumentParser(
        description='Download CDL raster',
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
