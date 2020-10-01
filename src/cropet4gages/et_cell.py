"""et_cell.py
Defines ETCellData class
Defines crop_cycle_mp, crop_cycle, crop_day_loop_mp, crop_day_loop,
    write_crop_output
Called by mod_crop_et.py

"""

from collections import defaultdict
import datetime
import logging
import math
import os
import re
import sys
import copy
import numpy as np
import pandas as pd
import shapefile

from src.cropet4gages import util

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '../../lib')))

mpdToMps = 3.2808399 * 5280 / 86400


class ETCellData():
    """Functions for loading ET Cell data from static text files

    Attributes
    ----------

    Notes
    -----

    """

    def __init__(self):
        """ """
        self.et_cells_dict = dict()
        self.crop_num_list = []
        self.et_cells_weather_data = {}
        self.et_cells_historic_data = {}

    def set_cell_properties(self, data):
        """Extract ET cells properties data from specified file

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        None

        Notes
        -----
        This function builds ETCell objects and must be run first

        """

        logging.info('\nReading ET Cells properties data from\n' +
                     data.cell_properties_path)
        try:
            df = pd.read_csv(data.cell_properties_path, engine='python',
                             sep=data.cell_properties_delimiter,
                             dtype={'ET Cell ID': str, 'ET Cell Name': str, 'Ref ET MET ID': str})
            uc_columns = list(df.columns)
            columns = [x.lower() for x in uc_columns]

            # remove excess baggage from column names

            columns = [x.replace(' (feet)', '').replace('in/hr', '').replace(
                'in/ft', '').replace(' - in', '').replace('decimal ', '') for
                       x in columns]
            columns = [x.replace('met ', '').replace(' - ', '').replace(
                " (a='coarse'  b='medium')", '').replace(
                " (1='coarse' 2='medium')", '') for x in columns]
            columns = [x.replace(' (fromhuntington plus google)', '').replace(
                '  ', ' ') for x in columns]

            # parse et cells properties for each cell
            for rc, row in df.iterrows():
                # row_list = row.tolist()
                cell = ETCell()
                if not (cell.read_cell_properties_from_row(row.tolist(), columns,
                                                           data.elev_units)):
                    sys.exit()
                self.et_cells_dict[cell.cell_id] = cell
        except:
            logging.error('Unable to read ET Cells Properties from ' +
                          data.cell_properties_path)
            logging.error('\nERROR: ' + str(sys.exc_info()[0]) + 'occurred\n')
            sys.exit()

    def set_cell_crops(self, data):
        """Read crop crop flags using specified file type

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        None

        Notes
        -----

        """

        self.read_cell_crops_txt(data)

    def read_cell_crops_txt(self, data):
        """Extract et cell crop data from text file

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        None

        Notes
        -----

        """

        logging.info('\nReading cell crop flags from\n' + data.cell_crops_path)
        all_data = pd.read_csv(data.cell_crops_path, dtype='str', sep=data.cell_crops_delimiter)
        cell_ids = all_data.iloc[:, 0].values
        irr_flags = all_data.iloc[:, 3].values
        crop_numbers = np.array(list(all_data.columns)[4:]).astype(int)
        a = all_data.iloc[:, 4:].values
        fao56_crop_file = data.crop_coefs_path
        crop_names = pd.read_csv(fao56_crop_file).values[:, 1]
        for i, row in enumerate(a):
            cell_id = cell_ids[i]
            if cell_id not in self.et_cells_dict.keys():
                logging.error('read_et_cells_crops(), cell_id %s not found'
                              % cell_id)
                sys.exit()
            cell = self.et_cells_dict[cell_id]
            # init_crops_from_row
            cell.irrigation_flag = int(irr_flags[i])
            cell.crop_flags = dict(zip(crop_numbers, row.astype(int) > 0))
            # self.crop_flags = dict(zip(crop_numbers, data[4:]))
            cell.ncrops = len(cell.crop_flags)

            cell.crop_names = crop_names
            cell.crop_numbers = crop_numbers
            # Make list of active crop numbers (i.e. flag is True) in cell

            cell.crop_num_list = sorted(
                [k for k, v in cell.crop_flags.items() if v])
            self.crop_num_list.extend(cell.crop_num_list)

        # Update list of active crop numbers in all cells

        self.crop_num_list = sorted(list(set(self.crop_num_list)))

    def set_cell_cuttings(self, data):
        """Extract mean cutting data from specified file

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        None

        Notes
        -----

        """

        logging.info('\nReading cell crop cuttings from\n' +
                     data.cell_cuttings_path)
        try:
            # Get list of 0 based line numbers to skip
            # Ignore header but assume header was set as 1's based index
            skiprows = [i for i in range(data.cell_cuttings_header_lines)
                        if i + 1 != data.cell_cuttings_names_line]

            df = pd.read_csv(data.cell_cuttings_path, engine='python', na_values=['NaN'],
                             header=data.cell_cuttings_names_line - len(skiprows) - 1,
                             skiprows=skiprows, sep=data.cell_cuttings_delimiter,
                             dtype={"ET Cell ID": str, "ET Cell Name": str})
            uc_columns = list(df.columns)
            columns = [x.lower() for x in uc_columns]
            cell_col = columns.index('et cell id')
            dairy_col = columns.index('number dairy')
            beef_col = columns.index('number beef')
            # parse et cells cuttings for each cell
            for rc, row in df.iterrows():
                row_list = row.tolist()

                # cell_id = row[cell_col]
                # cell_id = str(int(row[cell_col]))
                # Handle both str and float/int inputs and remove .0 decimal
                # https://docs.python.org/release/2.7.3/library/stdtypes.html#boolean-operations-and-or-not
                cell_id = (str(row[cell_col])[-2:] == '.0' and
                           str(row[cell_col])[:-2] or str(row[cell_col]))

                if cell_id not in self.et_cells_dict.keys():
                    logging.error('crop_et_data.static_mean_cuttings(), cell'
                                  '_id %s not found' % cell_id)
                    sys.exit()
                cell = self.et_cells_dict[cell_id]
                cell.dairy_cuttings = int(row[dairy_col])
                cell.beef_cuttings = int(row[beef_col])
        except:
            logging.error('Unable to read ET Cells cuttings from ' +
                          data.cell_cuttings_path)
            logging.error('\nERROR: ' + str(sys.exc_info()[0]) + 'occurred\n')
            sys.exit()

    def filter_crops(self, data):
        """filters crop list using crop_skip_list or crop_test_list from INI

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        None

        Notes
        -----

        """

        logging.info('\nFiltering crop lists')
        crop_numbers = set(self.crop_num_list)

        # Update master crop list
        if data.annual_skip_flag:
            annual_crops = set(
                crop_num
                for crop_num, crop_param in data.crop_params.items()
                if not crop_param.is_annual)
            crop_numbers &= annual_crops
            logging.info('  Active perennial crops: {}'.format(
                ', '.join(map(str, sorted(crop_numbers)))))
        if data.perennial_skip_flag:
            perennial_crops = set(
                crop_num
                for crop_num, crop_param in data.crop_params.items()
                if crop_param.is_annual)
            crop_numbers &= perennial_crops
            logging.info('  Active annual crops: {}'.format(
                ', '.join(map(str, sorted(crop_numbers)))))
        if data.crop_skip_list:
            logging.info('  Crop skip list: {}'.format(
                ', '.join(map(str, data.crop_skip_list))))
            crop_numbers -= set(data.crop_skip_list)
        if data.crop_test_list:
            logging.info('  Crop test list: {}'.format(
                ', '.join(map(str, data.crop_test_list))))
            crop_numbers &= set(data.crop_test_list)

        # Get max length of CELL_ID for formatting of log string
        cell_id_len = max([
            len(cell_id) for cell_id in self.et_cells_dict.keys()])

        # Filter each cell with updated master crop list
        for cell_id, cell in sorted(self.et_cells_dict.items()):
            cell.crop_num_list = sorted(
                crop_numbers & set(cell.crop_num_list))
            # Turn off the crop flag

            cell.crop_flags = {
                c: f and c in cell.crop_num_list
                for c, f in cell.crop_flags.items()}
            logging.info('  CellID: {1:{0}s}: {2}'.format(
                cell_id_len, cell_id,
                ', '.join(map(str, cell.crop_num_list))))

    def filter_cells(self, data):
        """Remove cells with no active crops

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        None

        Notes
        -----

        """

        logging.info('\nFiltering ET Cells')
        cell_ids = set(self.et_cells_dict.keys())
        if data.cell_skip_list:
            cell_ids -= set(data.cell_skip_list)
            logging.info('  Cell skip list: {}'.format(
                ','.join(map(str, data.cell_skip_list))))
        if data.cell_test_list:
            cell_ids &= set(data.cell_test_list)
            logging.info('  Cell test list: {}'.format(
                ','.join(map(str, data.cell_test_list))))

        # Get max length of CELL_ID for formatting of log string

        cell_id_len = max([
            len(cell_id) for cell_id in self.et_cells_dict.keys()])
        for cell_id, cell in sorted(self.et_cells_dict.items()):
            # Remove cells without any active crops

            if cell_id not in cell_ids:
                logging.info('  CellID: {1:{0}s} skipping'.format(
                    cell_id_len, cell_id))
                del self.et_cells_dict[cell_id]
            elif not set(self.crop_num_list) & set(cell.crop_num_list):
                logging.info('  CellID: {1:{0}s} skipping (no active crops)'.
                             format(cell_id_len, cell_id))
                del self.et_cells_dict[cell_id]

    def set_static_crop_params(self, crop_params):
        """set static crop parameters

        Parameters
        ---------
        crop_params :


        Returns
        -------
        None

        Notes
        -----

        """
        logging.info('\nSetting static crop parameters')

        # copy crop_params
        for cell_id in sorted(self.et_cells_dict.keys()):
            cell = self.et_cells_dict[cell_id]
            cell.crop_params = copy.deepcopy(crop_params)

    def set_static_crop_coeffs(self, crop_coeffs):
        """set static crop coefficients

        Parameters
        ---------
        crop_coeffs :


        Returns
        -------
        None

        Notes
        -----

        """

        logging.info('Setting static crop coefficients')
        for cell_id in sorted(self.et_cells_dict.keys()):
            cell = self.et_cells_dict[cell_id]
            cell.crop_coeffs = copy.deepcopy(crop_coeffs)

    def set_spatial_crop_params(self, calibration_ws):
        """set spatial crop parameters from spatial calibration

        Parameters
        ---------
        crop_coeffs :


        Returns
        -------
        None

        Notes
        -----

        """

        logging.info('Setting spatially varying crop parameters')
        cell_id_field = 'CELL_ID'
        crop_dbf_re = re.compile('crop_\d{2}_\w+.dbf$', re.I)

        # Get list of crop parameter shapefiles DBFs

        crop_dbf_dict = dict([
            (int(item.split('_')[1]), os.path.join(calibration_ws, item))
            for item in os.listdir(calibration_ws)
            if crop_dbf_re.match(item)])

        # Check to see if crop_dbf_dict is empty
        if not crop_dbf_dict:
            logging.error('\nSpatially Varying Calibration Files Do Not Exist.'
                          ' Run build_spatial_crop_params_arcpy.py')
            sys.exit()
            # return False

        # Filter the file list based on the "active" crops
        for crop_num in list(crop_dbf_dict):
            if crop_num not in self.crop_num_list:
                try:
                    del crop_dbf_dict[crop_num]
                except:
                    pass

        # Check to see that all "active" crops have shapefiles in spatially
        #  varying calibration folder
        missing_set = set(self.crop_num_list) - set(crop_dbf_dict.keys())
        # if self.crop_num_list not in crop_dbf_dict.keys():
        # ###WHY DOESN't THIS WORK (Data Type Issue???)
        if len(missing_set) > 0:
            logging.error(('\nMissing Crop Shapefiles In Calibration Folder. '
                           'Re-Run build_spatial_crop_params_arcpy.py'))
            missing_set_str = ', '.join(str(s) for s in missing_set)
            logging.error(('Missing Crops: ' + missing_set_str))
            sys.exit()
            # return False

        # DEADBEEF - This really shouldn't be hard coded here
        # Dictionary to convert shapefile field names to crop parameters
        param_field_dict = {
            'Name': 'name',
            'ClassNum': 'class_number',
            'IsAnnual': 'is_annual',
            'IrrigFlag': 'irrigation_flag',
            'IrrigDays': 'days_after_planting_irrigation',
            'Crop_FW': 'crop_fw',
            'WinterCov': 'winter_surface_cover_class',
            'CropKcMax': 'kc_max',
            'MAD_Init': 'mad_initial',
            'MAD_Mid': 'mad_midseason',
            'RootDepIni': 'rooting_depth_initial',
            'RootDepMax': 'rooting_depth_max',
            'EndRootGrw': 'end_of_root_growth_fraction_time',
            'HeightInit': 'height_initial',
            'HeightMax': 'height_max',
            'CurveNum': 'curve_number',
            'CurveName': 'curve_name',
            'CurveType': 'curve_type',
            'PL_GU_Flag': 'flag_for_means_to_estimate_pl_or_gu',
            'T30_CGDD': 't30_for_pl_or_gu_or_cgdd',
            'PL_GU_Date': 'date_of_pl_or_gu',
            'CGDD_Tbase': 'tbase',
            'CGDD_EFC': 'cgdd_for_efc',
            'CGDD_Term': 'cgdd_for_termination',
            'Time_EFC': 'time_for_efc',
            'Time_Harv': 'time_for_harvest',
            'KillFrostC': 'killing_frost_temperature',
            'InvokeStrs': 'invoke_stress',
            'CN_Coarse': 'cn_coarse_soil',
            'CN_Medium': 'cn_medium_soil',
            'CN_Fine': 'cn_fine_soil'}

        # Cuttings values can also be updated spatially
        cutting_field_dict = {
            'Beef_Cut': 'beef_cuttings',
            'Dairy_Cur': 'dairy_cuttings'}

        # Crop parameter shapefiles are by crop,
        #   but parameters need to be separated first by ETCell
        # Process each crop parameter shapefile

        for crop_num, crop_dbf in sorted(crop_dbf_dict.items()):
            logging.debug('    {0:2d} {1}'.format(crop_num, crop_dbf))

            # Process using dbfread
            # crop_f = DBF(crop_dbf)
            # for record in crop_f:
            #     _id = record[cell_id_field]
            #      field_name, row_value in dict(record).items():

            # Process using shapefile/pyshp

            crop_f = shapefile.Reader(crop_dbf)
            crop_fields = [f[0] for f in crop_f.fields if f[0] !=
                           'DeletionFlag']

            for record in crop_f.iterRecords():
                # convert cell_id from .shp to str to match etcells type
                cell_id = str(record[crop_fields.index(cell_id_field)])

                # Skip cells
                if cell_id not in self.et_cells_dict.keys():
                    logging.info('CellID: {} not in et cell list. Not reading spatial'
                                 ' crop parameters for this cell.'.format(
                        cell_id))
                    continue
                for field_name, row_value in zip(crop_fields, record):
                    # DEADBEEF - I really want to skip non-crop parameter fields
                    # but also tell the user if a crop param field is missing

                    try:
                        param_name = param_field_dict[field_name]
                    except:
                        param_name = None
                    try:
                        cutting_name = cutting_field_dict[field_name]
                    except:
                        cutting_name = None
                    if param_name is not None:
                        try:
                            setattr(
                                self.et_cells_dict[cell_id].crop_params[
                                    crop_num], param_name, float(row_value))
                            # print(self.et_cells_dict[cell_id].crop_params[
                            #         crop_num], param_name, float(row_value))

                        except:
                            logging.warning(
                                ('  The spatial crop parameter was not '
                                 'updated\n' + '    cell_id:    {0}\n'
                                               '    crop_num:   {1}\n' +
                                 '    field_name: {2}\n    parameter:  {3}').
                                    format(cell_id, crop_num, field_name,
                                           param_name))
                    elif cutting_name is not None:
                        try:
                            setattr(
                                self.et_cells_dict[cell_id],
                                cutting_name, float(row_value))
                        except:
                            logging.warning(
                                ('  The spatial cutting parameter was not '
                                 'updated\n' +
                                 '    cell_id:    {0}\n    crop_num:   {1}\n' +
                                 '    field_name: {2}\n    parameter:  {3}').
                                    format(cell_id, crop_num, field_name,
                                           cutting_name))
        return True


class ETCell():
    """ET cells property container

    Attributes
    ----------

    Notes
    -----

    """

    def __init__(self):
        """ """
        pass

    def __str__(self):
        """ """
        return '<ETCell {0}, {1} {2}>'.format(
            self.cell_id, self.cell_name, self.refet_id)

    def read_cell_properties_from_row(self, row, columns, elev_units='feet'):
        """ Parse row of data from ET Cells properties file

        Parameters
        ---------
        row : list
            one row of ET Cells Properties
        start_column : int
            first zero based row column

        Returns
        -------
        : boolean
            True
            False

        """
        # ET Cell id is cell id for crop and area et computations
        # Ref ET MET ID is met node id, aka ref et node id of met and ref et row

        if 'et cell id' in columns:
            self.cell_id = str(row[columns.index('et cell id')])
        else:
            logging.error('Unable to read ET Cell id')
            return False
        if 'et cell name' in columns:
            self.cell_name = str(row[columns.index('et cell name')])
        else:
            self.cell_name = self.cell_id
        if 'ref et id' in columns:
            self.refet_id = row[columns.index('ref et id')]
        else:
            logging.error('Unable to read reference et id')
            return False
        if 'latitude' in columns:
            self.latitude = float(row[columns.index('latitude')])
        else:
            logging.error('Unable to read latitude')
            return False
        if 'longitude' in columns:
            self.longitude = float(row[columns.index('longitude')])
        else:
            logging.error('Unable to read longitude')
            return False
        if 'elevation' in columns:
            self.elevation = float(row[columns.index('elevation')])
            if elev_units == 'feet' or elev_units == 'ft':
                self.elevation *= 0.3048
        else:
            logging.error('Unable to read elevation')
            return False

        # Compute air pressure of station/cell
        self.air_pressure = util.pair_from_elev(0.3048 * self.elevation)
        if 'area weighted average permeability' in columns:
            self.permeability = float(row[columns.index('area weighted average'
                                                        ' permeability')])
        else:
            logging.error('Unable to read area weighted average permeability')
            return False
        if 'area weighted average whc' in columns:
            self.stn_whc = float(row[columns.index('area weighted average'
                                                   ' whc')])
        else:
            logging.error('Unable to read area weighted average WHC')
            return False
        if 'average soil depth' in columns:
            self.stn_soildepth = float(row[columns.index('average soil depth')])
        else:
            logging.error('Unable to read average soil depth')
            return False
        if 'hydrologic group (a-c)' in columns:
            self.stn_hydrogroup_str = str(row[columns.index('hydrologic group'
                                                            ' (a-c)')])
        else:
            logging.error('Unable to read Hydrologic Group (A-C)')
            return False
        if 'hydrologic group (1-3)' in columns:
            self.stn_hydrogroup = int(row[columns.index('hydrologic group'
                                                        ' (1-3)')])
        else:
            logging.error('Unable to read Hydrologic Group (1-3)')
            return False
        if 'aridity rating' in columns:
            self.aridity_rating = float(row[columns.index('aridity rating')])
        else:
            logging.error('Unable to read elevation')
            return False
        """
        # Additional optional meta row
        # These items were in vb.net version to support previous vb6 versions.
        # Not yet used in python but could be useful for specifying
        # an alternative source of data.

        self.refet_row_path = None
        if 'refet row path' in columns:
            if not pd.isnull(row[columns.index('refet row path')]):
                if len(row[columns.index('refet row path')]) > 3:
                    self.refet_row_path = row[columns.index('refet row path')]
        self.source_refet_id = self.cell_id
        if 'source refet id' in columns:
            if not pd.isnull(row[columns.index('source refet id')]):
                if len(row[columns.index('source refet id')]) > 0:
                    self.source_refet_id = row[columns.index('source refet id')]
        """
        return True

    def set_input_timeseries(self, cell_count, data, cells):
        """Wrapper for setting all refet and met data

        Parameters
        ---------
        cell_count : int
            count of et cell being processed
        data : dict
            configuration data from INI file
        cells : dict
            eT cells data

        Returns
        -------
        : boolean
            True
            False

        """

        if not self.set_refet_data(data, cells):
            return False
        if data.refet_ratios_path:
            self.set_refet_ratio_data(data)
        if not self.set_weather_data(cell_count, data, cells):
            return False

        # Process climate arrays
        self.process_climate(data)
        return True

    def set_refet_data(self, data, cells):
        """Read ETo/ETr data file for single station

        Parameters
        ---------
        cell_count :
            count of et cell being processed
        data : dict
            configuration data from INI file
        cells : dict
            et cells data

        Returns
        -------
        : boolean
            True
            False

        """

        logging.debug('\nRead ETo/ETr data')

        logging.debug('Read meteorological/climate data')
        # if data.refet['data_structure_type'].upper() == 'SF P':
        success = self.SF_P_refet_data(data)
        # else:
        #     success = self.DMI_refet_data(data, cells)
        if not success:
            logging.error('Unable to read reference ET data.')
            return False

        # Check/modify units

        for field_key, field_units in data.refet['units'].items():
            if field_units is None:
                continue
            elif field_units.lower() in ['mm', 'mm/day', 'mm/d']:
                continue
            elif field_units.lower() == 'in*100':
                self.refet_df[field_key] *= 0.254
            elif field_units.lower() == 'in':
                self.refet_df[field_key] *= 25.4
            elif field_units.lower() == 'inches/day':
                self.refet_df[field_key] *= 25.4
            elif field_units.lower() == 'in/day':
                self.refet_df[field_key] *= 25.4
            elif field_units.lower() == 'm':
                self.refet_df[field_key] *= 1000.0
            elif field_units.lower() in ['m/d', 'm/day']:
                if field_key == 'wind':
                    self.refet_df[field_key] /= 86400
                else:
                    self.refet_df[field_key] *= 1000.0
            elif field_units.lower() in ['mpd', 'miles/d', 'miles/day']:
                self.refet_df[field_key] /= mpdToMps
            else:
                logging.error('\n ERROR: Unknown {0} units {1}'.format(
                    field_key, field_units))

        # set date attributes
        self.refet_df['doy'] = [int(ts.strftime('%j')) for ts in
                                self.refet_df.index]
        return True

    def SF_P_refet_data(self, data):
        """Read meteorological/climate data for single station with all
            parameters

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        : boolean
            True
            False
        """

        refet_path = os.path.join(data.refet['ws'], data.refet['name_format'] % self.refet_id)
        logging.debug('  {0}'.format(refet_path))

        # Get list of 0 based line numbers to skip
        # Ignore header but assume header was set as a 1's based index
        skiprows = [i for i in range(data.refet['header_lines']) if i + 1 != data.refet['names_line']]
        try:
            self.refet_df = pd.read_csv(refet_path, engine='python',
                                        header=data.refet['names_line'] - len(skiprows) - 1, skiprows=skiprows,
                                        delimiter=data.refet['delimiter'])
        except IOError:
            logging.error(
                ('  IOError: RefET data file could not be read ' + 'and may not exist\n  {}').format(refet_path))
            sys.exit()
        except:
            logging.error('  Unknown error reading RefET data file\n {}'.format(refet_path))
            sys.exit()
        logging.debug('  Columns: {}'.format(', '.join(list(self.refet_df.columns))))

        # Check that fields exist in data table
        for field_key, field_name in data.refet['fields'].items():
            if field_name is not None and field_name not in self.refet_df.columns:
                logging.error(
                    '\n  ERROR: Field "{0}" was not found in {1}\n    Check{2}_field value inINI file'.format(
                        field_name, os.path.basename(refet_path), field_key))
                sys.exit()

            # Rename dataframe fields
            self.refet_df = self.refet_df.rename(columns={field_name: field_key})

        # Convert date strings to datetimes
        if data.refet['fields']['date'] is not None:
            self.refet_df['date'] = pd.to_datetime(self.refet_df['date'])
        else:
            self.refet_df['date'] = self.refet_df[['year', 'month', 'day']].apply(lambda s: datetime.datetime(*s),
                                                                                  axis=1)
        self.refet_df.set_index('date', inplace=True)

        # truncate period
        try:
            self.refet_df = self.refet_df.truncate(before=data.start_dt, after=data.end_dt)
        except:
            logging.error('\nERROR: ' + str(sys.exc_info()[0]) + 'occurred truncating weather data')
            return False
        if len(self.refet_df.index) < 1:
            logging.error('No data found reading ret data')
            return False
        return True

    def set_refet_ratio_data(self, data):
        """Read ETo/ETr ratios static file

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        : boolean
            True
            False

        Notes
        -----

        """

        logging.info('  Reading ETo/ETr ratios')
        try:
            refet_ratios_df = pd.read_csv(data.refet_ratios_path, delimiter=data.et_ratios_delimiter, header='infer',
                                          skiprows=data.et_ratios_header_lines - 1, na_values=['NaN'])
            del refet_ratios_df[data.et_ratios_name_field]
        except IOError:
            logging.error('  IOError: ETo ratios static file could not be read and may not exist\n  {}'.format(
                data.refet_ratios_path))
            sys.exit()
        except:
            logging.error('  Unknown error reading ETo ratios static file\n {}'.format(data.refet_ratios_path))
            sys.exit()

        # Remove duplicates
        # If there are duplicate station IDs, for now only use first instance
        # Eventually allow users to tie station IDs to cells
        if refet_ratios_df.duplicated(subset=data.et_ratios_id_field).any():
            logging.warning(
                'There are duplicate station IDs in ETo Ratios file\n'
                'Only the first instance of station ID will be applied')
            refet_ratios_df.drop_duplicates(subset=data.et_ratios_id_field, inplace=True)

        # Flatten/flip data so that ratio values are in one column
        refet_ratios_df = pd.melt(refet_ratios_df, id_vars=[data.et_ratios_id_field],
                                  var_name=data.et_ratios_month_field, value_name=data.et_ratios_ratio_field)
        refet_ratios_df[data.et_ratios_ratio_field] = refet_ratios_df[data.et_ratios_ratio_field].astype(np.float)

        # Set any missing values to 1.0
        refet_ratios_df.fillna(value=1.0, inplace=True)

        # Convert month abbreviations to numbers
        refet_ratios_df[data.et_ratios_month_field] = [datetime.datetime.strptime(m, '%b').month for m in
                                                       refet_ratios_df[data.et_ratios_month_field]]

        # Filter to current station
        refet_ratios_df = refet_ratios_df[refet_ratios_df[data.et_ratios_id_field] == self.refet_id]
        if refet_ratios_df.empty:
            logging.warning('  Empty table, ETo/ETr ratios not applied')
            return False

        # Set month as index
        refet_ratios_df.set_index(data.et_ratios_month_field, inplace=True)
        logging.info(refet_ratios_df)

        # Scale ETo/ETr values
        # Is 'Month' vs 'month' change needed?
        # Input climate files have Year, Month, Day.
        # add 'month' column if not in df for ratio join
        if 'month' not in self.refet_df:
            logging.info('month_field not specified in REFET section of .ini and default "month" column not found.'
                         ' Creating month column from date/index for refet data/ratio join.')
            self.refet_df['month'] = self.refet_df.index.month
        self.refet_df = self.refet_df.join(refet_ratios_df, 'month')
        self.refet_df['etref'] *= self.refet_df[data.et_ratios_ratio_field]
        del self.refet_df[data.et_ratios_ratio_field]
        del self.refet_df[data.et_ratios_month_field]
        del self.refet_df[data.et_ratios_id_field]
        return True

    def set_weather_data(self, cell_count, data, cells):
        """Read meteorological data for single station and fill missing
            values

        Parameters
        ---------
        cell_count :
            count of et cell being processed
        data : dict
            configuration data from INI file
        cells : dict
            et cells data

        Returns
        -------
        : boolean
            True
            False

        Notes
        -----

        """

        logging.debug('Read meteorological/climate data')
        # if data.weather['data_structure_type'].upper() == 'SF P':
        success = self.SF_P_weather_data(data)
        # else:
        #     success = self.DMI_weather_data(cell_count, data, cells)
        if not success:
            logging.error('Unable to read and fill daily metereorological '
                          'data.')
            return False

        # Check/modify units
        # GROUP UNIT CHANGES AND COMMENT !!!
        for field_key, field_units in data.weather['units'].items():
            if field_units is None:
                continue
            elif field_units.lower() in ['c', 'mm', 'mm/day', 'm/s', 'mps', 'mj/m2', 'mj/m^2', 'kg/kg', 'kpa', '%']:
                continue
            elif field_units.lower() == 'k':
                self.weather_df[field_key] -= 273.15
            elif field_units.lower() == 'f':
                self.weather_df[field_key] -= 32
                self.weather_df[field_key] /= 1.8
            elif field_units.lower() == 'in*100':
                self.weather_df[field_key] *= 0.254
            elif field_units.lower() == 'in':
                self.weather_df[field_key] *= 25.4
            elif field_units.lower() == 'inches/day':
                self.weather_df[field_key] *= 25.4
            elif field_units.lower() == 'in/day':
                self.weather_df[field_key] *= 25.4
            # pressure unit conversions (add more)
            elif field_units.lower() == 'mmhg':
                self.weather_df[field_key] *= 0.133322
            elif field_units.lower() == 'm':
                self.weather_df[field_key] *= 1000.0
            elif field_units.lower() in ['m/d', 'm/day']:
                if field_key == 'wind':
                    self.weather_df[field_key] /= 86400
                else:
                    self.weather_df[field_key] *= 1000.0
            elif field_units.lower() == 'meter':
                self.weather_df[field_key] *= 1000.0
            elif field_units.lower() in ['mpd', 'miles/d', 'miles/day']:
                self.weather_df[field_key] /= mpdToMps
            else:
                logging.error('\n ERROR: Unknown {0} units {1}'.format(field_key, field_units))

        # set date attributes
        self.weather_df['doy'] = [int(ts.strftime('%j')) for ts in self.weather_df.index]

        # Scale wind height to 2m if necessary
        if data.weather['wind_height'] != 2:
            self.weather_df['wind'] *= (4.87 / np.log(67.8 * data.weather['wind_height'] - 5.42))

        return True

    def SF_P_weather_data(self, data):
        """Read meteorological/climate data for single station with all
            parameters

        Parameters
        ---------
        data : dict
            configuration data from INI file

        Returns
        -------
        : boolean
            True
            False

        Notes
        -----

        """

        weather_path = os.path.join(data.weather['ws'], data.weather['name_format'] % self.refet_id)
        logging.debug('  {0}'.format(weather_path))

        # Get list of 0 based line numbers to skip
        # Ignore header but assume header was set as 1's based index
        skiprows = [i for i in range(data.weather['header_lines']) if i + 1 != data.weather['names_line']]
        try:
            self.weather_df = pd.read_csv(weather_path, engine='python',
                                          header=data.weather['names_line'] - len(skiprows) - 1,
                                          skiprows=skiprows, delimiter=data.weather['delimiter'])
        except IOError:
            logging.error(
                '  IOError: Weather data file could not be read and may not exist\n  {}'.format(weather_path))
            return False
            # sys.exit()
        except:
            logging.error('  Unknown error reading Weather data file\n {}'.format(weather_path))
            return False
            # sys.exit()
        logging.debug('  Columns: {0}'.format(', '.join(list(self.weather_df.columns))))

        # Check fields

        for field_key, field_name in data.weather['fields'].items():
            if field_name is not None and field_name not in self.weather_df.columns:
                logging.error(
                    '\n  ERROR: Field "{0}" was not found in {1}\n    Check{2}_field value inINI file'.format(
                        field_name, os.path.basename(weather_path), field_key))
                return False
            # Rename dataframe field
            self.weather_df = self.weather_df.rename(columns={field_name: field_key})

        # Convert date strings to datetimes
        if data.weather['fields']['date'] is not None:
            self.weather_df['date'] = pd.to_datetime(self.weather_df['date'])
        else:
            self.weather_df['date'] = self.weather_df[['year', 'month', 'day']].apply(lambda s: datetime.datetime(*s),
                                                                                      axis=1)
        self.weather_df.set_index('date', inplace=True)

        # truncate period
        try:
            self.weather_df = self.weather_df.truncate(before=data.start_dt, after=data.end_dt)
        except:
            logging.error('\nERROR: ' + str(sys.exc_info()[0] + 'occurred truncating weather data'))
            return False
        if len(self.weather_df.index) < 1:
            logging.error('No data found reading weather data')
            return False
        return True

    def process_climate(self, data):
        """process meterological data into climate data
            a) Compute long term averages (DAY LOOP)
                adjust and check temperature data
                process alternative TMax and TMin
            b) Fill missing data with long term doy average (DAY LOOP)
                Calculate an estimated depth of snow on ground using simple
                melt rate function))
                compute main cumGDD for period of record for various bases for
                constraining earliest/latest planting or GU
                only Tbase = 0 needs to be evaluated (used to est. GU for alfalfa,
                 mint, hops)
            c) compute long term mean cumGDD0 from sums (JDOY LOOP)

        Parameters
        ---------
        data : dict
            data from INI file

        Returns
        -------
        : boolean
            True
            False

        Notes
        -----
        Time series data have reversed field names support historic (constant)
         phenology
        maxt, mint, meant, 30T are historic equivalents of tmax, tmin,
        meant, t30
        Cumulative variables use 'hist' in lieu of 'main'

        """
        self.climate_df = self.weather_df[['doy', 'ppt', 'tmax', 'tmin', 'wind', 'rh_min']].copy()

        self.climate_df['maxt'] = self.weather_df['tmax'].values
        self.climate_df['mint'] = self.weather_df['tmin'].values
        del self.weather_df

        # pick up reference et
        self.climate_df['etref'] = self.refet_df['etref'].values

        # T30 stuff - done after temperature adjustments
        self.climate_df['tmean'] = self.climate_df[["tmax", "tmin"]].mean(axis=1)
        self.climate_df['meant'] = self.climate_df[["maxt", "mint"]].mean(axis=1)
        # self.climate_df['t30'] = pd.rolling_mean(self.climate_df['tmean'],
        #  window = 30, min_periods = 1)
        self.climate_df['t30'] = self.climate_df['tmean'].rolling(window=30, min_periods=1).mean()
        # self.climate_df['30t'] = pd.rolling_mean(self.climate_df['meant'],
        #  window = 30, min_periods = 1)
        self.climate_df['30t'] = self.climate_df['meant'].rolling(window=30, min_periods=1).mean()

        # Accumulate T30 over period of record
        main_t30_lt = np.array(self.climate_df[['t30', 'doy']].groupby('doy').mean()['t30'])
        hist_t30_lt = np.array(self.climate_df[['30t', 'doy']].groupby('doy').mean()['30t'])

        # Compute GDD for each day
        # self.climate_df['main_cgdd'] = self.climate_df['tmean']
        # self.climate_df.ix[self.climate_df['tmean'] <= 0, 'main_cgdd'] = 0
        # self.climate_df['hist_cgdd'] = self.climate_df['meant']
        # self.climate_df.ix[self.climate_df['tmean'] <= 0, 'hist_cgdd'] = 0

        # Replacement for .ix deprecation above 4/22/2020
        self.climate_df['main_cgdd'] = self.climate_df['tmean']
        self.climate_df.loc[self.climate_df['tmean'] <= 0, 'main_cgdd'] = 0
        self.climate_df['hist_cgdd'] = self.climate_df['meant']
        self.climate_df.loc[self.climate_df['tmean'] <= 0, 'hist_cgdd'] = 0

        # Compute cumulative GDD for each year
        self.climate_df['main_cgdd'] = self.climate_df[['doy', 'main_cgdd']].groupby(
            self.climate_df.index.map(lambda x: x.year)).main_cgdd.cumsum()
        self.climate_df['hist_cgdd'] = self.climate_df[['doy', 'hist_cgdd']].groupby(
            self.climate_df.index.map(lambda x: x.year)).hist_cgdd.cumsum()

        # Compute mean cumulative GDD for each DOY
        main_cgdd_0_lt = np.array(self.climate_df[['main_cgdd', 'doy']].groupby('doy').mean()['main_cgdd'])
        hist_cgdd_0_lt = np.array(self.climate_df[['hist_cgdd', 'doy']].groupby('doy').mean()['hist_cgdd'])

        # Revert from indexing by I to indexing by DOY (for now)
        # Copy DOY 1 value into DOY 0

        main_t30_lt = np.insert(main_t30_lt, 0, main_t30_lt[0])
        main_cgdd_0_lt = np.insert(main_cgdd_0_lt, 0, main_cgdd_0_lt[0])
        hist_t30_lt = np.insert(hist_t30_lt, 0, hist_t30_lt[0])
        hist_cgdd_0_lt = np.insert(hist_cgdd_0_lt, 0, hist_cgdd_0_lt[0])

        self.climate = {}
        self.climate['main_t30_lt'] = main_t30_lt
        self.climate['main_cgdd_0_lt'] = main_cgdd_0_lt
        self.climate['hist_t30_lt'] = hist_t30_lt
        self.climate['hist_cgdd_0_lt'] = hist_cgdd_0_lt

        return True


if __name__ == '__main__':
    pass
