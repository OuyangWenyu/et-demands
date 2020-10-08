"""initialize_crop_cycle.py
Defines InitializeCropCycle class
Called by crop_cycle.py

"""

import logging
import numpy as np


class InitializeCropCycle:
    def __init__(self):
        """Initialize for crops cycle"""
        self.cgdd = 0.
        self.cgdd_penalty = 0.
        self.etc_act = 0.
        self.etc_pot = 0.
        self.etc_bas = 0.
        self.etref_30 = 0.  # thirty day mean ETref  ' added 12/2007
        self.gdd = 0.0
        self.gdd_penalty = 0.
        self.height_min = 0.
        self.height_max = 0.
        self.height = 0
        self.kc_act = 0.
        self.kc_pot = 0
        self.kc_max = 0.
        self.kc_min = 0.
        self.kc_bas = 0.
        self.kc_bas_mid = 0.
        self.kc_bas_prev = 0.
        self.mad = 0.
        self.mad_ini = 0.
        self.mad_mid = 0.
        self.n_cgdd = 0.
        self.n_pl_ec = 0.

        # CGM - I don't remember why these are grouped separately
        # Maybe because they are "flags"
        self.doy_start_cycle = 0
        self.cutting = 0
        self.cycle = 1
        self.real_start = False
        self.irr_flag = False
        self.in_season = False  # false if outside season, true if inside
        self.dormant_setup_flag = False
        self.crop_setup_flag = True  # flag to setup crop parameter information

        # CGM - These are not pre-initialized in the 32-bit VB code
        self.cgdd_at_planting = 0.

        # CGM - Initialized to 0 in latest VB code
        self.kc_bas_prev = 0.

        # TP - Added
        self.max_lines_in_crop_curve_table = 34

        # CGM - In VB code, crops 44-46 were run first to set these values kn kcb_daily()
        #   Initialize here instead
        #   Using a dictionary instead of an array to make the indexing more obvious
        self.kc_bas_wscc = dict()
        self.kc_bas_wscc[1] = 0.1
        self.kc_bas_wscc[2] = 0.1
        self.kc_bas_wscc[3] = 0.1

    def crop_load(self, data, et_cell, cdl_fao_etd_crop_num):
        """Assign characteristics for crop from crop Arrays
        Parameters
        ---------
        data : dict
            configuration data from INI file

        et_cell :

        cdl_fao_etd_crop_num : list
            cdl, fao56 and etd crop's type number

        Returns
        -------
        None

        Notes
        -----
        Called by crop_cycle.crop_cycle() just before time loop

        """
        crop = data.crop_params[abs(cdl_fao_etd_crop_num[2])]
        self.height_min = crop.height_initial
        self.height_max = crop.height_max

        self.height = self.height_min

        # Find maximum kc_bas in array for this crop (used later in height calc)
        # kc_bas_mid is the maximum kc_bas found in the kc_bas table read into program
        # Following code was repaired to properly parse crop curve arrays on 7/31/2012.  dlk

        self.kc_mid = 0.

        # Bare soil etd=44, mulched soil etd=45, dormant turf/sod (winter) etd=46 do not have curve

        if crop.curve_number > 0:
            fao_crop_num = [int(i) for i in cdl_fao_etd_crop_num[1].split(",")]
            if len(fao_crop_num) > 1:
                self.kc_mid = np.mean([et_cell.crop_coeffs[j]["Kc mid"] for j in fao_crop_num])
            else:
                self.kc_mid = et_cell.crop_coeffs[fao_crop_num[0]]["Kc mid"]

        # Irrigation flag
        # CGM - How are these different?
        # For flag=1 or 2, turn irrigation on for a generally 'irrigated' region
        # For flag=3, turn irrigation on for specific irrigated crops even in non-irrigated region
        # Added Jan 2007 to force grain and turf irrigation in rainfed region
        if crop.irrigation_flag >= 1:
            self.irr_flag = True  # turn irrigation on for a generally 'irrigated' region
        # Either no irrigations for this crop or station or
        #      irrigation off even in irrigated region if this crop has no flag
        else:
            self.irr_flag = False  # no irrigations for this crop or station

        # Pre-compute parameters instead of re-computing them daily

        # Flag_for_means_to_estimate_pl_or_gu Case 1

        if crop.flag_for_means_to_estimate_pl_or_gu == 1:
            cgdd_col = 'hist_cgdd_0_lt'
            try:
                self.longterm_pl = int(np.where(
                    np.diff(np.array(et_cell.climate[cgdd_col] > crop.t30_for_pl_or_gu_or_cgdd, dtype=np.int8)) > 0)[0][
                                           0]) + 1
            except:
                logging.error(('  initialize_crop_cycle():\n  Crop: {0:2d}, CellID: {1}\n' +
                               '  Error computing longterm_pl, CGDD (LT) didn\'t go above threshold ({2})\n' +
                               '  Setting longerm_pl = 0').format(crop.class_number, et_cell.cell_id,
                                                                  crop.t30_for_pl_or_gu_or_cgdd))
                self.longterm_pl = 0

        # Flag_for_means_to_estimate_pl_or_gu Case 2

        elif crop.flag_for_means_to_estimate_pl_or_gu == 2:
            t30_col = 'hist_t30_lt'
            try:
                # This logic fails when the T30 never goes below t30_for_pl_or_gu_or_cgdd
                # Report wrong error message
                self.longterm_pl = int(np.where(
                    np.diff(np.array(et_cell.climate[t30_col] > crop.t30_for_pl_or_gu_or_cgdd, dtype=np.int8)) > 0)[0][
                                           0]) + 1

            except IndexError:
                self.longterm_pl = 0
                logging.error(('  initialize_crop_cycle(): \n  Crop: {0:2d}, CellID: {1}\n' +
                               '  Error computing longterm_pl, T30 (LT) didn\'t go above threshold ({2})\n' +
                               '  Setting longerm_pl = 0').format(crop.class_number, et_cell.cell_id,
                                                                  crop.t30_for_pl_or_gu_or_cgdd))
                logging.info('  Station long term T30:')
                logging.info(et_cell.climate['main_t30_lt'])
                self.longterm_pl = 0
            except:
                self.longterm_pl = 0
                logging.error(('  initialize_crop_cycle():\n' +
                               '  Crop: {0:2d}, CellID: {1}\n' +
                               '  Unknown error computing longterm_pl\n' +
                               '  Setting longerm_pl = 0').format(crop.class_number, et_cell.cell_id))
        self.setup_crop(crop)

    def setup_crop(self, crop):
        """Initialize some variables for beginning of crop seasons

        Attributes
        ----------
        crop :


        Returns
        -------
        None

        Notes
        -----
        Called in crop_cycle if not in season and crop setup flag is true
        Called in kc_daily for startup/greenup type 1, 2, and 3 when startup conditions are met

        """
        # setup_crop is called from crop_cycle if is_season is false and crop_setup_flag is true
        # thus only setup 1st time for crop (not each year)
        # also called from kcb_daily each time GU/Plant date is reached, thus at growing season start
        self.height_min = crop.height_initial
        self.height_max = crop.height_max
        self.height = self.height_min
        self.crop_setup_flag = False

    def setup_dormant(self, et_cell, crop):
        """Start of dormant season
            a) Set up for soil water reservoir during non-growing season
                to collect soil moisture for next growing season
            b) Set for type of surface during non-growing season

        Parameters
        ---------
        et_cell :

        crop :

        Returns
        -------
        None

        Notes
        -----
        Called at termination of crop from crop_cycle()
        If in_season is false and dormant_flag is true,
        dormant_flag set at GU each year.
        It is called each year as soon as season is 0.

        """

        # winter_surface_cover_class = 1 bare, 2 mulch, 3 sod
        wscc = crop.winter_surface_cover_class

        # Kc_bas for wintertime land use
        #  44: Bare soil
        #  45: Mulched soil, including wheat stubble
        #  46: Dormant turf/sod (winter time)
        #  note: set Kcmax for winter time (Nov-Mar) and fc outside of this sub.

        if wscc == 1:
            self.kc_bas = 0.1  # was 0.2
        elif wscc == 2:
            self.kc_bas = 0.1  # was 0.2
        elif wscc == 3:
            self.kc_bas = 0.2  # was 0.3

        self.dormant_setup_flag = False

        # Clear cutting flag (just in case)
        self.cutting = 0

    def setup_dataframe(self, et_cell):
        """Initialize output dataframe

        Attributes
        ----------
        et_cell :


        Returns
        -------

        Notes
        -----

        """

        self.crop_df = et_cell.refet_df[['doy', 'etref']].copy()
        self.crop_df['et_act'] = np.nan
        self.crop_df['et_pot'] = np.nan
        self.crop_df['et_bas'] = np.nan
        self.crop_df['kc_act'] = np.nan
        self.crop_df['kc_bas'] = np.nan
        self.crop_df['season'] = 0
        self.crop_df['cutting'] = 0
