"""crop_et_data.py
Defines CropETData class
Functions in class to read INI file, refet data, met data, ...
Called by mod_crop_et.py

"""

import configparser
import logging
import os
import pandas as pd
import sys

from src.cropet4gages import crop_coefficients, crop_parameters, util


class CropETData:
    """Crop et data container

    Attributes
    ----------

    """

    def __init__(self):
        """ """

    def __str__(self):
        """ """
        return '<Cropet_data>'

    def read_cet_ini(self, config, debug_flag=False):
        """Read and parse INI file
        Parameters
        ---------
        config : config_cet
        debug_flag : boolean
            True : write debug level comments to debug.txt
            False

        Returns
        -------

        Notes
        -----

        """
        # Check that all sections are present
        crop_et_sec = 'CROP_ET'  # required
        weather_sec = 'WEATHER'  # required
        refet_sec = 'REFET'  # required

        cfg_secs = list(config.keys())

        # verify existence of common required sections
        if crop_et_sec not in cfg_secs or refet_sec not in cfg_secs or weather_sec not in cfg_secs:
            logging.error('\nERROR:input file must have following sections:\n [{}], [{}], and [{}]'.format(crop_et_sec,
                                                                                                           weather_sec,
                                                                                                           refet_sec))

        # project specifications
        try:
            self.project_ws = config.CROP_ET.project_folder
        except:
            logging.error('ERROR: project_folder parameter is not set in INI file')
            sys.exit()

        # project folder needs to be full/absolute path
        # check existence
        if not os.path.isdir(self.project_ws):
            logging.critical('ERROR:project folder does not exist\n  %s' % self.project_ws)
            sys.exit()

        # Basin
        try:
            self.basin_id = config.CROP_ET.basin_id
            if self.basin_id is None or self.basin_id == 'None':
                self.basin_id = 'Default Basin'
        except:
            self.basin_id = 'Default Basin'
        logging.info('  Basin: {}'.format(self.basin_id))

        # Timestep -
        self.time_step = 'day'

        # Timestep quantity - specify an integer
        self.ts_quantity = int(1)

        # user starting date
        try:
            sdt = config.CROP_ET.start_date
            if sdt == 'None':
                sdt = None
        except:
            sdt = None
        if sdt is None:
            self.start_dt = None
        else:
            self.start_dt = pd.to_datetime(sdt)

        # ending date
        try:
            edt = config.CROP_ET.end_date
            if edt == 'None':
                edt = None
        except:
            edt = None
        if edt is None:
            self.end_dt = None
        else:
            self.end_dt = pd.to_datetime(edt)

        # static (aka) meta data specifications
        try:
            self.static_folder = config.CROP_ET.static_folder
            if self.static_folder is None or self.static_folder == 'None':
                logging.warning("Static workspace set to default 'static'")
                self.static_folder = 'static'
        except:
            logging.warning("Static workspace set to default 'static'")
            self.static_folder = 'static'
        if not os.path.isdir(self.static_folder):
            self.static_folder = os.path.join(self.project_ws, self.static_folder)

        # elevation units
        try:
            self.elev_units = config.CROP_ET.elev_units
            if self.elev_units is None or self.elev_units == 'None':
                self.elev_units = 'feet'
        except:
            self.elev_units = 'feet'

        # usda cdl crop name
        self.cdl_crop_class_path = config.CROP_ET.cdl_crop_class_path
        self.cdl_crosswalk_fao56_etd_path = config.CROP_ET.cdl_crosswalk_fao56_etd_path

        # et cells properties
        try:
            cell_properties_name = config.CROP_ET.cell_properties_name
            if cell_properties_name is None or cell_properties_name == 'None':
                logging.error('ERROR: ET Cells properties data file must be specified')
                sys.exit()
        except:
            logging.error('ERROR:  ET Cells properties data file must be specified')
            sys.exit()

        # test joined path
        self.cell_properties_path = os.path.join(self.static_folder, cell_properties_name)
        if not os.path.isfile(self.cell_properties_path):
            self.cell_properties_path = cell_properties_name

            # test if fully specified path
            if not os.path.isfile(self.cell_properties_path):
                logging.error('ERROR:  ET Cells properties file {} does not exist'.format(self.cell_properties_path))
                sys.exit()
        logging.info('  ET Cell Properties file: {}'.format(self.cell_properties_path))

        self.cell_properties_delimiter = '\t'
        self.cell_properties_ws = ''
        self.cell_properties_names_line = 1
        self.cell_properties_header_lines = 1

        # et cells crops
        try:
            cell_crops_name = config.CROP_ET.cell_crops_name
            if cell_crops_name is None or cell_crops_name == 'None':
                logging.error('ERROR:  ET Cells crops data file must be specified')
                sys.exit()
        except:
            logging.error('ERROR:  ET Cells crops data file must be specified')
            sys.exit()
        self.cell_crops_path = os.path.join(self.static_folder, cell_crops_name)
        if not os.path.isfile(self.cell_crops_path):
            self.cell_crops_path = cell_crops_name
            if not os.path.isfile(self.cell_crops_path):
                logging.error('ERROR:  ET Cells crops file {} does not exist'.format(self.cell_crops_path))
                sys.exit()
        logging.info('  ET Cell crops file: {}'.format(self.cell_crops_path))

        self.cell_crops_delimiter = '\t'
        self.cell_crops_ws = ''
        self.cell_crops_header_lines = 3
        self.cell_crops_names_line = 2

        # et cells cuttings
        try:
            cell_cuttings_name = config.CROP_ET.cell_cuttings_name
            if cell_cuttings_name is None or cell_cuttings_name == 'None':
                logging.error('ERROR:  ET Cells cuttings data file must be specified')
                sys.exit()
        except:
            logging.error('ERROR:  ET Cells cuttings data file must be specified')
            sys.exit()
        self.cell_cuttings_path = os.path.join(self.static_folder, cell_cuttings_name)
        if not os.path.isfile(self.cell_cuttings_path):
            self.cell_cuttings_path = cell_cuttings_name
            if not os.path.isfile(self.cell_cuttings_path):
                logging.error('ERROR:  ET Cells cuttings file {} does not exist'.format(self.self.cell_cuttings_path))
                sys.exit()
        logging.info('  ET Cell cuttings file: {}'.format(self.cell_cuttings_path))

        self.cell_cuttings_delimiter = '\t'
        self.cell_cuttings_ws = ''
        self.cell_cuttings_header_lines = 2
        self.cell_cuttings_names_line = 2

        # set crop parameter specs
        try:
            crop_params_name = config.CROP_ET.crop_params_name
            if crop_params_name is None or crop_params_name == 'None':
                logging.error('ERROR:  Crop parameters data file must be specified')
                sys.exit()
        except:
            logging.error('ERROR:  Crop parameters data file must be specified')
            sys.exit()
        self.crop_params_path = os.path.join(self.static_folder, crop_params_name)
        if not os.path.isfile(self.crop_params_path):
            self.crop_params_path = crop_params_name
            if not os.path.isfile(self.crop_params_path):
                logging.error('ERROR:  crop parameters file {} does not exist'.format(self.crop_params_path))
                sys.exit()
        logging.info('  Crop parameters file: {}'.format(self.crop_params_path))

        self.crop_params_delimiter = '\t'
        self.crop_params_ws = ''
        self.crop_params_header_lines = 4
        self.crop_params_names_line = 3

        # set additional crop params, the key points of 4 stages
        self.crop_key_points_file = config.CROP_ET.crop_key_points_file

        # set crop coefficient specs
        try:
            crop_coefs_name = config.CROP_ET.crop_coefs_name
            if crop_coefs_name is None or crop_coefs_name == 'None':
                logging.error('ERROR:  Crop coefficients data file must be specified')
                sys.exit()
        except:
            logging.error('ERROR:  Crop coefficients data file must be specified')
            sys.exit()
        # self.crop_coefs_path = os.path.join(self.static_folder, crop_coefs_name)
        self.crop_coefs_path = config.CROP_ET.crop_coefs_path
        if not os.path.isfile(self.crop_coefs_path):
            self.crop_coefs_path = crop_coefs_name
            if not os.path.isfile(self.crop_coefs_path):
                logging.error('ERROR:  crop coefficients file {} does not exist'.format(self.self.crop_coefs_path))
                sys.exit()
        logging.info('  Crop coefficients file: {}'.format(self.crop_coefs_path))

        self.crop_coefs_delimiter = '\t'
        self.crop_coefs_ws = ''
        self.crop_coefs_names_line = 1
        self.crop_coefs_header_lines = 1

        # reference ET adjustment ratios
        try:
            et_ratios_name = config.CROP_ET.et_ratios_name
            self.refet_ratios_path = os.path.join(self.static_folder, et_ratios_name)
        except configparser.NoOptionError:
            logging.info('\net_ratios_name not found in INI. Setting to None.')
            self.refet_ratios_path = None

        if self.refet_ratios_path and not os.path.isfile(
                self.refet_ratios_path):
            logging.error('Warning:  ET Ratios file not found. ET scaling will not be applied.')
            self.refet_ratios_path = None

        # Default et_ratios file format
        self.et_ratios_delimiter = '\t'
        self.et_ratios_ws = ''
        self.et_ratios_header_lines = 1
        self.et_ratios_names_line = 1
        self.et_ratios_id_field = 'Met Node ID'
        self.et_ratios_name_field = 'Met Node Name'
        self.et_ratios_month_field = 'month'
        self.et_ratios_ratio_field = 'ratio'

        """
        INI [CROP_ET] Section

        """
        # cet output flags
        self.cet_out = {}
        try:
            self.cet_out['daily_output_flag'] = config.CROP_ET.daily_stats_flag
        except:
            logging.debug('    daily_stats_flag = False')
            self.cet_out['daily_output_flag'] = False
        try:
            self.cet_out['monthly_output_flag'] = config.CROP_ET.monthly_stats_flag
        except:
            logging.debug('    monthly_stats_flag = False')
            self.cet_out['monthly_output_flag'] = False
        try:
            self.cet_out['annual_output_flag'] = config.CROP_ET.annual_stats_flag
        except:
            logging.debug('    annual_stats_flag = False')
            self.cet_out['annual_output_flag'] = False
        try:
            self.gs_output_flag = config.CROP_ET.growing_season_stats_flag
        except:
            logging.debug('    growing_season_stats_flag = False')
            self.gs_output_flag = False

        #  Allow user to only run annual or perennial crops
        try:
            self.annual_skip_flag = config.CROP_ET.annual_skip_flag
        except:
            logging.info('    annual_skip_flag = False')
            self.annual_skip_flag = False
        try:
            self.perennial_skip_flag = config.CROP_ET.perennial_skip_flag
        except:
            logging.info('    perennial_skip_flag = False')
            self.perennial_skip_flag = False

        # For testing, allow user to process a subset of crops
        try:
            self.crop_skip_list = list(util.parse_int_set(config.CROP_ET.crop_skip_list))
        except:
            logging.debug('    crop_skip_list = []')
            self.crop_skip_list = []
        try:
            self.crop_test_list = list(util.parse_int_set(config.CROP_ET.crop_test_list))
        except:
            logging.debug('    crop_test_list = False')
            self.crop_test_list = []

        # Bare soils must be in crop list for computing winter cover
        if self.crop_test_list:
            self.crop_test_list = sorted(list(set(self.crop_test_list + [44, 45, 46])))

        # For testing, allow the user to process a subset of cells
        try:
            self.cell_skip_list = config.CROP_ET.cell_skip_list.split(',')
            self.cell_skip_list = [c.strip() for c in self.cell_skip_list]
        except:
            logging.debug('    cell_skip_list = []')
            self.cell_skip_list = []
        try:
            self.cell_test_list = config.CROP_ET.cell_test_list.split(',')
            self.cell_test_list = [c.strip() for c in self.cell_test_list]
        except:
            logging.debug('    cell_test_list = False')
            self.cell_test_list = []

        # Input/output folders
        if self.cet_out['daily_output_flag']:
            try:
                self.cet_out['daily_output_ws'] = os.path.join(self.project_ws, config.CROP_ET.daily_output_folder)
                if not os.path.isdir(self.cet_out['daily_output_ws']):
                    os.makedirs(self.cet_out['daily_output_ws'])
            except:
                logging.debug('    daily_output_folder = daily_stats')
                self.cet_out['daily_output_ws'] = 'daily_stats'
        if self.cet_out['monthly_output_flag']:
            try:
                self.cet_out['monthly_output_ws'] = os.path.join(self.project_ws, config.CROP_ET.monthly_output_folder)
                if not os.path.isdir(self.cet_out['monthly_output_ws']):
                    os.makedirs(self.cet_out['monthly_output_ws'])
            except:
                logging.debug('    monthly_output_folder = monthly_stats')
                self.cet_out['monthly_output_ws'] = 'monthly_stats'
        if self.cet_out['annual_output_flag']:
            try:
                self.cet_out['annual_output_ws'] = os.path.join(self.project_ws, config.CROP_ET.annual_output_folder)
                if not os.path.isdir(self.cet_out['annual_output_ws']):
                    os.makedirs(self.cet_out['annual_output_ws'])
            except:
                logging.debug('    annual_output_folder = annual_stats')
                self.cet_out['annual_output_ws'] = 'annual_stats'
        if self.gs_output_flag:
            try:
                self.gs_output_ws = os.path.join(self.project_ws, config.CROP_ET.gs_output_folder)
                if not os.path.isdir(self.gs_output_ws):
                    os.makedirs(self.gs_output_ws)
            except:
                logging.debug('    gs_output_folder = growing_season_stats')
                self.gs_output_ws = 'growing_season_stats'

        # cet file type specifications
        self.cet_out['file_type'] = 'csv'
        # self.cet_out['data_structure_type'] = "DRI"
        self.cet_out['name_format'] = '%s_crop_%c.csv'
        self.cet_out['header_lines'] = 1
        self.cet_out['names_line'] = 1
        self.cet_out['delimiter'] = ','

        # pick up user growing season file specifications
        if self.gs_output_flag:
            self.gs_name_format = self.cet_out['name_format'].replace('%s', '%s_gs')

        """
        Computational switches
            False : sets crop 1 to alfalfa peak with no cuttings
            True : sets crop 1 to nonpristine alfalfa w/cuttings

        """
        try:
            self.crop_one_flag = config.CROP_ET.crop_one_flag
        except:
            self.crop_one_flag = True

        # crop one (alfalfa) reduction factor
        try:
            self.crop_one_reducer = config.CROP_ET.crop_one_reducer
        except:
            self.crop_one_reducer = 0.9

        # Compute additional variables
        try:
            self.cutting_flag = config.CROP_ET.cutting_flag
        except:
            self.cutting_flag = True
        try:
            self.niwr_flag = config.CROP_ET.niwr_flag
        except:
            self.niwr_flag = True
        try:
            self.kc_flag = config.CROP_ET.kc_flag
        except:
            self.kc_flag = True

        # added 8/2020 to allow for growing season start doy to progress unchecked (no limit)
        try:
            self.gs_limit_flag = config.CROP_ET.gs_limit_flag
        except:
            self.gs_limit_flag = True

        # Spatially varying calibration
        try:
            self.spatial_cal_flag = config.CROP_ET.spatial_cal_flag
        except:
            self.spatial_cal_flag = False
        try:
            self.spatial_cal_ws = config.CROP_ET.spatial_cal_folder
        except:
            self.spatial_cal_ws = None
        if self.spatial_cal_flag and self.spatial_cal_ws is not None and not os.path.isdir(self.spatial_cal_ws):
            logging.error('ERROR:spatial calibration folder {} does not exist'.format(self.spatial_cal_ws))
            sys.exit()

        # output date formats and values formats
        try:
            self.cet_out['daily_date_format'] = config.CROP_ET.daily_date_format
            if self.cet_out['daily_date_format'] is None or self.cet_out['daily_date_format'] == 'None':
                self.cet_out['daily_date_format'] = '%Y-%m-%d'
        except:
            self.cet_out['daily_date_format'] = '%Y-%m-%d'
        try:
            self.cet_out['daily_float_format'] = config.CROP_ET.daily_float_format
            if self.cet_out['daily_float_format'] == 'None':
                self.cet_out['daily_float_format'] = None
        except:
            self.cet_out['daily_float_format'] = None
        try:
            self.cet_out['monthly_date_format'] = config.CROP_ET.monthly_date_format
            if self.cet_out['monthly_date_format'] is None or self.cet_out['monthly_date_format'] == 'None':
                self.cet_out['monthly_date_format'] = '%Y-%m'
        except:
            self.cet_out['monthly_date_format'] = '%Y-%m'
        try:
            self.cet_out['monthly_float_format'] = config.CROP_ET.monthly_float_format
            if self.cet_out['monthly_float_format'] == 'None':
                self.cet_out['monthly_float_format'] = None
        except:
            self.cet_out['monthly_float_format'] = None
        try:
            self.cet_out['annual_date_format'] = config.CROP_ET.annual_date_format
            if self.cet_out['monthly_date_format'] is None or self.cet_out['monthly_date_format'] == 'None':
                self.cet_out['annual_date_format'] = '%Y'
        except:
            self.cet_out['annual_date_format'] = '%Y'
        try:
            self.cet_out['annual_float_format'] = config.CROP_ET.annual_float_format
            if self.cet_out['annual_float_format'] == 'None':
                self.cet_out['annual_float_format'] = None
        except:
            self.cet_out['annual_float_format'] = None

        """
        INI [REFET] Section

        """
        self.refet = {}
        self.refet['fields'] = {}
        self.refet['units'] = {}
        self.refet['ws'] = config.REFET.refet_folder
        # refet folder could be full or relative path
        # Assume relative paths or from project folder

        if os.path.isdir(self.refet['ws']):
            pass
        elif not os.path.isdir(self.refet['ws']) and os.path.isdir(os.path.join(self.project_ws, self.refet['ws'])):
            self.refet['ws'] = os.path.join(self.project_ws, self.refet['ws'])
        else:
            logging.error('ERROR:refet folder {} does not exist'.format(self.refet['ws']))
            sys.exit()

        self.refet['type'] = config.REFET.refet_type.lower()
        if self.refet['type'] not in ['eto', 'etr']:
            logging.error('  ERROR: RefET type must be ETo or ETr')
            sys.exit()

        self.refet['file_type'] = 'csv'
        # self.refet['data_structure_type'] = 'SF P'
        self.refet['name_format'] = config.REFET.name_format
        self.refet['header_lines'] = config.REFET.header_lines
        self.refet['names_line'] = config.REFET.names_line
        try:
            self.refet['delimiter'] = config.REFET.delimiter
            if self.refet['delimiter'] is None or self.refet['delimiter'] == 'None':
                self.refet['delimiter'] = ','
            else:
                if self.refet['delimiter'] not in [' ', ',', '\\t']:
                    self.refet['delimiter'] = ','
                if "\\" in self.refet['delimiter'] and "t" in self.refet['delimiter']:
                    self.refet['delimiter'] = self.refet['delimiter'].replace('\\t', '\t')
        except:
            self.refet['delimiter'] = ','

        # Field names and units
        # Date can be read directly or computed from year, month, and day
        try:
            self.refet['fields']['date'] = config.REFET.date_field
        except:
            self.refet['fields']['date'] = None
        try:
            self.refet['fields']['year'] = config.REFET.year_field
            self.refet['fields']['month'] = config.REFET.month_field
            self.refet['fields']['day'] = config.REFET.day_field
        except:
            self.refet['fields']['year'] = None
            self.refet['fields']['month'] = None
            self.refet['fields']['day'] = None
        if self.refet['fields']['date'] is not None:
            logging.debug('  REFET: Reading date from date column')
        elif (self.refet['fields']['year'] is not None and
              self.refet['fields']['month'] is not None and
              self.refet['fields']['day'] is not None):
            logging.debug('\nREFET: Reading date from year, month, and day columns')
        else:
            logging.error('  ERROR: REFET date_field (or year, month, and day fields) must be set in INI')
            sys.exit()
        try:
            self.refet['fields']['etref'] = config.REFET.etref_field
        except:
            logging.error('  ERROR: REFET etref_field must set in INI')
            sys.exit()
        try:
            self.refet['fnspec'] = config.REFET.etref_name
            if self.refet['fnspec'] is None or self.refet['fnspec'] == 'None':
                self.refet['fnspec'] = self.refet['fields']['etref']
        except:
            self.refet['fnspec'] = self.refet['fields']['etref']
        try:
            self.refet['units']['etref'] = config.REFET.etref_units
        except:
            logging.error('  ERROR: REFET etref_units must set in INI')
            sys.exit()

        # Check RefET parameters
        if not os.path.isdir(self.refet['ws']):
            logging.error('  ERROR:RefET data folder does not exist\n  %s' % self.refet['ws'])
            sys.exit()

        # Check fields and units
        elif self.refet['units']['etref'].lower() not in ['mm/day', 'mm']:
            logging.error('  ERROR:  Ref ET units {0} are not currently supported'.format(self.refet['units']['etref']))
            sys.exit()

        """
        INI [WEATHER] Section

        """
        # Weather parameters
        self.weather = {}
        self.weather['fields'] = {}
        self.weather['units'] = {}

        # fnspec - parameter extension to file name specification
        self.weather['fnspec'] = {}
        self.weather['wsspec'] = {}
        self.weather['ws'] = config.WEATHER.weather_folder

        # weather folder could befull or relative path
        # Assume relative paths or fromproject folder
        if os.path.isdir(self.weather['ws']):
            pass
        elif (not os.path.isdir(self.weather['ws']) and
              os.path.isdir(os.path.join(self.project_ws, self.weather['ws']))):
            self.weather['ws'] = os.path.join(self.project_ws, self.weather['ws'])
        else:
            logging.error('ERROR:refet folder {} does not exist'.format(self.weather['ws']))
            sys.exit()

        self.weather['file_type'] = 'txt'
        # self.weather['data_structure_type'] = 'SF P'
        self.weather['name_format'] = config.WEATHER.name_format
        self.weather['header_lines'] = config.WEATHER.header_lines
        self.weather['names_line'] = config.WEATHER.names_line
        try:
            self.weather['delimiter'] = config.WEATHER.delimiter
            if self.weather['delimiter'] is None or self.weather['delimiter'] == 'None':
                self.weather['delimiter'] = ','
            else:
                if self.weather['delimiter'] not in [' ', ',', '\\t']:
                    self.weather['delimiter'] = ','
                if "\\" in self.weather['delimiter'] and "t" in self.weather['delimiter']:
                    self.weather['delimiter'] = self.weather['delimiter'].replace('\\t', '\t')
        except:
            self.weather['delimiter'] = ','

        # Field names and units
        # Date can be read directly or computed from year, month, and day
        try:
            self.weather['fields']['date'] = config.WEATHER.date_field
        except:
            self.weather['fields']['date'] = None
        try:
            self.weather['fields']['year'] = config.WEATHER.year_field
            self.weather['fields']['month'] = config.WEATHER.month_field
            self.weather['fields']['day'] = config.WEATHER.day_field
        except:
            self.weather['fields']['year'] = None
            self.weather['fields']['month'] = None
            self.weather['fields']['day'] = None
        if self.weather['fields']['date'] is not None:
            logging.debug('  WEATHER: Reading date from date column')
        elif (self.weather['fields']['year'] is not None and
              self.weather['fields']['month'] is not None and
              self.weather['fields']['day'] is not None):
            logging.debug('  WEATHER: Reading date from year, month,'
                          ' and day columns')
        else:
            logging.error('  ERROR: WEATHER date_field (or year, month, and ' +
                          'day fields) must be set in INI')
            sys.exit()

        # Field names
        field_list = ['tmin', 'tmax', 'ppt', 'wind', 'rh_min']
        for f_name in field_list:
            try:
                self.weather['fields'][f_name] = eval('config.WEATHER.' + f_name + '_field')
            except:
                logging.error('  ERROR: WEATHER {}_field must be set in INI'.format(f_name))
                sys.exit()

        # Units
        for f_name in field_list:
            if f_name == 'date':
                continue
            elif self.weather['fields'][f_name] is not None:
                try:
                    self.weather['units'][f_name] = eval('config.WEATHER.' + f_name + '_units')
                except:
                    logging.error('  ERROR: WEATHER {}_units must be set in INI'.format(f_name))
                    sys.exit()

        # fnspec
        for f_name in field_list:
            if f_name == 'date':
                continue
            elif self.weather['fields'][f_name] is not None:
                try:
                    self.weather['fnspec'][f_name] = eval('config.WEATHER.' + f_name + '_name')
                except:
                    self.weather['fnspec'][f_name] = f_name
            else:
                self.weather['fnspec'][f_name] = 'Unused'

        # Wind speeds measured at heights other than 2 meters will be scaled
        try:
            self.weather['wind_height'] = config.WEATHER.wind_height
        except:
            self.weather['wind_height'] = 2

        # Check weather parameters
        if not os.path.isdir(self.weather['ws']):
            logging.error('  ERROR:weather data folder does not exist\n  %s' % self.weather['ws'])
            sys.exit()

        # REPLACE WITH CODE IN units.py TAKEN FROM WSWUP/REFET
        # Check units
        units_list = ['c', 'mm', 'mm/d', 'mm/day', 'm/d', 'm', 'meter',
                      'in*100', 'in', 'in/day', 'inches/day', 'kg/kg', 'kpa',
                      'mmhg', 'k', 'f', 'm/s', 'mps', 'mpd', 'miles/day',
                      'miles/d', "%"]
        for k, v in self.weather['units'].items():
            if v is not None and v.lower() not in units_list:
                logging.error('  ERROR: {0} units {1} are not currently supported'.format(k, v))
                sys.exit()

        # Check if refet_type matches crop_coefs_name
        if self.refet['type'] not in self.crop_coefs_path.lower():
            logging.warning('\nRefET Type does not match crop_coefs file name. Check the ini')
            logging.info('  refet_type = {}'.format(self.refet['type']))
            logging.info('  crop_coefs_name = {}'.format(self.crop_coefs_path))
            input('Press ENTER to continue or Ctrl+C to exit')

    def set_crop_params(self):
        """ List of <CropParameter> instances

        Parameters
        ---------
        None

        Returns
        -------
        None

        """

        logging.info('  Reading crop parameters from\n' + self.crop_params_path)

        params_df = pd.read_csv(self.crop_params_path, delimiter=self.crop_params_delimiter, header=None,
                                skiprows=self.crop_params_header_lines - 1, na_values=['NaN'])
        params_df.applymap(str)
        params_df.fillna('0', inplace=True)

        crop_params_addition = pd.read_csv(self.crop_key_points_file)

        self.crop_params = {}
        for crop_i in range(2, len(list(params_df.columns))):
            crop_param_data = params_df[crop_i].values.astype(str)
            crop_num = abs(int(crop_param_data[1]))
            # read NCGDD for development/NCGDD for late season
            # and Time percent to EFC for development/Time percent to EFC for late season/Days after EFC for late season
            crop_addition = crop_params_addition.iloc[crop_i - 2, [11, 12, 15, 16, 17]]
            self.crop_params[crop_num] = crop_parameters.CropParameters(crop_param_data, crop_addition)

        # Filter crop parameters based on skip and test lists
        # Filtering could happen in read_crop_parameters()

        if self.crop_skip_list or self.crop_test_list:
            # Leave bare soil "crop" parameters
            # Used in initialize_crop_cycle()

            non_crop_list = [44]
            # non_crop_list = [44,45,46,55,56,57]
            self.crop_params = {
                k: v for k, v in self.crop_params.items()
                if ((self.crop_skip_list and k not in self.crop_skip_list) or
                    (self.crop_test_list and k in self.crop_test_list) or
                    (k in non_crop_list))}

        print("read crop params")

    def set_crop_coeffs(self):
        """ List of <CropCoeff> instances

        Parameters
        ---------
        None

        Returns
        -------
        None

        """

        logging.info('  Reading crop coefficients')
        self.crop_coeffs = crop_coefficients.read_fao56_crop_coefs(self)


def console_logger(logger=logging.getLogger(''), log_level=logging.INFO):
    # Create console logger
    logger.setLevel(log_level)
    log_console = logging.StreamHandler(stream=sys.stdout)
    log_console.setLevel(log_level)
    log_console.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(log_console)
    return logger


# CHECK THAT INI USED IN TESTS EXISTS AND IS UP TO DATE
def do_tests():
    # Simple testing of functions as developed
    # logger = console_logger(log_level = 'DEBUG')
    logger = console_logger(log_level=logging.DEBUG)
    ini_path = os.getcwd() + os.sep + "cet_template.ini"
    cfg = CropETData()
    cfg.read_cet_ini(ini_path, True)


if __name__ == '__main__':
    # testing during development
    do_tests()
