"""kcb_daily.py
Defines kcb_daily function
Called by crop_cycle.py

"""

import datetime
import logging
import sys
import numpy as np


def kc_daily(data, et_cell, crop, foo, foo_day, debug_flag=False):
    """Compute ET using Kc method

    Parameters
    ---------
        data :

        et_cell :
        crop :
        foo :
        foo_day :

        debug_flag : boolean
            True : write debug level comments to debug.txt
            False

    Returns
    -------
    None

    Notes
    -----

    """

    # Added 8/2020
    # True: limit gs start to +/-40 days of long term avg (case 1 and 2 only)
    # False: no limit on gs start
    # gs_limit sets the threshold for gs start doy relative to long-term avg
    # flag = True sets gs start doy to +/-40 of long-term avg
    # flag = False applies no limit to gs start doy
    if data.gs_limit_flag:
        # 40 allows start day to be +/-40 days of long-term average
        # 40 is the threshold from original ET Demands code
        gs_limit = 40
    else:
        # 365 days allow for start day to be any doy
        gs_limit = 365

    # Determine if inside or outside growing period
    # Procedure for deciding start and return false of season.
    curve_number = crop.curve_number

    # Determination of start of season was rearranged April 12 2009 by R.Allen
    # To correct computation error in limiting first and latest starts of season
    #   that caused a complete loss of crop start turnon.

    # XXX Need to reset Realstart = false twice in Climate Sub.

    # Flag for estimating start of season
    # 1 = cgdd, 2 = t30, 3 = date, 4 or 0 is on alltime
    if debug_flag:
        logging.debug(
            'kcb_daily(): Flag_for_means_to_estimate_pl_or_gu %d' % crop.flag_for_means_to_estimate_pl_or_gu)
        logging.debug('kcb_daily(): kc_bas %.6f  kc_bas_prev %.6f' % (foo.kc_bas, foo.kc_bas_prev))

    # Flag_for_means_to_estimate_pl_or_gu Case 1

    if crop.flag_for_means_to_estimate_pl_or_gu == 1:
        # Only allow start flag to begin if < July 15
        # to prevent GU in fall after freezedown
        if foo_day.doy < (crop.gdd_trigger_doy + 195):
            # Before finding date of startup using normal cgdd,
            #   determine if it is after latest allowable start
            #   by checking to see if pl or gu need to be constrained
            #   based on long term means estimate date based on long term mean:
            # Prohibit specifying start of season as long term less 40 days
            #   when it is before that date.

            # Check if getting too late in season
            # Season hasn't started yet
            # was longterm_pl + 40 ----4/30/2009
            if foo.longterm_pl > 0 and foo_day.doy > (foo.longterm_pl + 40) and not foo.real_start:
                foo.doy_start_cycle = foo_day.doy
                foo.real_start = True

            # Start of season has not yet been determined.
            # Look for it in normal fashion:

            if not foo.real_start and foo.cgdd > crop.t30_for_pl_or_gu_or_cgdd:
                # JH,RGA 4/13/09
                # if cgdd > t30_for_pl_or_gu_or_cgdd(ctCount) And
                #    lcumGDD < t30_for_pl_or_gu_or_cgdd(ctCount) Then
                #   was until 4/13/09.
                # last part not needed now, with Realstart 'JH,RGA
                # planting or GU is today

                # This is modelled startup day, but check to see if it is too early
                # use +/- 40 days from longterm as constraint
                if foo.longterm_pl > 0 and foo_day.doy < (foo.longterm_pl - 40):
                    foo.real_start = False  # too early to start season
                    foo.doy_start_cycle = foo.longterm_pl - 40
                    if foo.doy_start_cycle < 1:
                        foo.doy_start_cycle += 365
                else:
                    foo.doy_start_cycle = foo_day.doy
                    foo.real_start = True

            # If season start has been found then turn parameters on
            # Look for day when DoY equals doy_start_cycle
            # Note that this requires that all days be present (no missing days)

            if foo_day.doy == foo.doy_start_cycle:
                foo.real_start = True
                foo.in_season = True
                foo.dormant_setup_flag = True
                foo.setup_crop(crop)

                # First cycle for alfalfa
                foo.cycle = 1

                # Some range grasses require backing up 10 days
                # Note that following logic will cause first 10 days to not
                #   be assigned to range grasses, but to winter cover
                #   but this code needs to be here because process (or DoY)
                #   can not go back in time

                if crop.date_of_pl_or_gu < 0.0:
                    foo.doy_start_cycle += int(crop.date_of_pl_or_gu)
                    if foo.doy_start_cycle < 1:
                        foo.doy_start_cycle = foo.doy_start_cycle + 365
            if debug_flag:
                logging.debug('kcb_daily(): in_season %d  longterm_pl %d  doy %d  doy_start_cycle %d' %
                              (foo.in_season, foo.longterm_pl, foo_day.doy, foo.doy_start_cycle))
                logging.debug('kcb_daily(): t30_for_pl_or_gu_or_cgdd %.6f' % crop.t30_for_pl_or_gu_or_cgdd)

    # Flag_for_means_to_estimate_pl_or_gu Case 2
    elif crop.flag_for_means_to_estimate_pl_or_gu == 2:
        # Use T30 for startup
        # Caution - need some constraints for oscillating T30 and for late summer
        # Use first occurrence
        if foo_day.doy < (crop.gdd_trigger_doy + 195):
            # Only allow start flag to begin if < July 15 to prevent GU
            #   in fall after freeze down before finding date of startup
            #   using normal T30, determine if it is after latest
            #   allowable start by checking to see if pl or gu
            #   need to be constrained based on long term means
            # Estimate date based on long term mean
            # Prohibit specifying start of season as long term less
            #   40 days when it is before that date.

            # Check if getting too late in season and season hasn't started yet

            # if (foo.longterm_pl > 0 and
            #     foo_day.doy > (foo.longterm_pl + 40) and
            # not foo.real_start):

            # added gs_limit_flag 8/2020 to allow start doy to extend freely
            if foo.longterm_pl > 0 and foo_day.doy > (foo.longterm_pl + gs_limit) and not foo.real_start:
                # longterm_pl + 40 'it is unseasonably warm (too warm).
                # Delay start ' set to Doy on 4/29/09 (nuts)
                foo.doy_start_cycle = foo_day.doy
                foo.real_start = True  # Harleys Rule
                logging.debug('kcb_daily(): doy_start_cycle %d  It is unseasonably warm (too warm) Harleys Rule' %
                              foo.doy_start_cycle)

            # Start of season has not yet been determined.
            # Look for it in normal fashion:
            # use +/- 40 days from longterm as constraint
            if not foo.real_start:
                if foo_day.t30 > crop.t30_for_pl_or_gu_or_cgdd:  # 'JH,RGA 4/13/09
                    # added gs_limit_flag and theshold options to allow for  start dates
                    # to extend unbounded by long term average
                    if foo.longterm_pl > 0 and foo_day.doy < (foo.longterm_pl - gs_limit):
                        foo.real_start = False  # too early to start season
                        if data.gs_limit_flag:
                            foo.doy_start_cycle = foo.longterm_pl - 40
                        else:
                            # Set start day to 1 if foo_day is negative and gs_limit_flag is False
                            # Can this be happen?
                            foo.doy_start_cycle = 1
                        logging.debug('kcb_daily(): doy_start_cycle %d  Start is too early' % foo.doy_start_cycle)
                        if foo.doy_start_cycle < 1:
                            foo.doy_start_cycle += 365
                    else:
                        foo.doy_start_cycle = foo_day.doy
                        foo.real_start = True

            # If season start has been found then turn parameters on
            #   look for day when DoY equals doy_start_cycle
            # Note that this requires that all days be present
            # (no missing days)
            if foo_day.doy == foo.doy_start_cycle:
                foo.real_start = True
                foo.in_season = True
                foo.dormant_setup_flag = True
                foo.setup_crop(crop)
                foo.cycle = 1  # first cycle for alfalfa

                # some range grasses require backing up 10 days
                # note that following logic will cause first 10 days
                # to not be assigned to range grasses, but to winter cover
                # but this code needs to be here because process (or doy)
                # can not go back in time
                if crop.date_of_pl_or_gu < 0.0:
                    foo.doy_start_cycle += int(crop.date_of_pl_or_gu)
                    if foo.doy_start_cycle < 1:
                        foo.doy_start_cycle += 365

            if debug_flag:
                logging.debug('kc_daily(): longterm_pl %d' % foo.longterm_pl)
                logging.debug('kc_daily(): doy_start_cycle %d  doy %d  real_start %d' %
                              (foo.doy_start_cycle, foo_day.doy, foo.real_start))
                logging.debug('kc_daily(): T30 %.6f  t30_for_pl_or_gu_or_cgdd %.6f  Date_of_pl_or_gu %s' %
                              (foo_day.t30, crop.t30_for_pl_or_gu_or_cgdd, crop.date_of_pl_or_gu))
                logging.debug('kc_daily(): in_season %d' % foo.in_season)

    # Flag_for_means_to_estimate_pl_or_gu Case 3
    elif crop.flag_for_means_to_estimate_pl_or_gu == 3:
        # Compute planting or green-up date from fractional month
        # Putting in a date_of_pl_or_gu of "1" will return Jan. 15th
        # Putting in a date_of_pl_or_gu of "10" will return Oct. 15th
        # Putting in a date_of_pl_or_gu of "4.8333" will return Apr. 25th
        month_of_pl_or_gu = int(crop.date_of_pl_or_gu)
        day_of_pl_or_gu = int(round((crop.date_of_pl_or_gu - month_of_pl_or_gu) * 30.4))
        if day_of_pl_or_gu < 0.5:
            day_of_pl_or_gu = 15
        if month_of_pl_or_gu == 0:
            date_of_pl_or_gu = 12
            logging.info('  Changing date_of_pl_or_gu from 0 to 12')

        # Planting or greenup day of year
        doy = datetime.datetime(foo_day.year, month_of_pl_or_gu, day_of_pl_or_gu).timetuple().tm_yday

        # Modified next statement to get winter grain to et and irrigate in first year of run.  dlk  08/16/2012
        # TODO: dont't know why the original code "or (foo_day.sdays == 1 and doy >= crop.gdd_trigger_doy):" exists
        if foo_day.doy == doy:
            foo.doy_start_cycle = doy
            foo.in_season = True
            foo.dormant_setup_flag = True
            # Initialize rooting depth, etc. for crop
            foo.setup_crop(crop)
        logging.debug('kc_daily(): in_season %d' % foo.in_season)

    # Flag_for_means_to_estimate_pl_or_gu Case 4
    elif crop.flag_for_means_to_estimate_pl_or_gu == 4:
        foo.in_season = True
        foo.dormant_setup_flag = True
        logging.debug('kc_daily(): in_season %d' % foo.in_season)

    else:
        logging.error('\nERROR: kc_daily() Unrecognized flag_for_means_to_estimate_pl_or_gu value')
        sys.exit()

    # InSeason
    if foo.in_season:
        # print('In-Season')
        # <------This kc loop only conducted if inside growing season
        # crop curve type:
        # 1 = NcumGDD, 2 = %PL-EC, 3 = %PL-EC, daysafter, 4 = %PL-Term

        kc_curve_num = et_cell.crop_num_list[0]
        kc_ini = et_cell.crop_coeffs[kc_curve_num]["Kc ini"]
        kc_mid = et_cell.crop_coeffs[kc_curve_num]["Kc mid"]
        kc_end = et_cell.crop_coeffs[kc_curve_num]["Kc end"]

        # crop.curve_type Case 1 ####
        if crop.curve_type == 1:
            # Normalized cumulative growing degree days
            if debug_flag:
                logging.debug('kc_daily(): cropclass_num %d  crop_one_flag %d  cycle %d' %
                              (crop.class_number, data.crop_one_flag, foo.cycle))

            if foo.doy_start_cycle == foo_day.doy:
                foo.cgdd_at_planting = foo.cgdd
            cgdd_in_season = max(0, foo.cgdd - foo.cgdd_at_planting)
            # Notice!: CGDD(EFF or TERM) is the specified crop-dependent value for CGDD
            # from the time of planting or greenup to the attainment of effective full cover or termination
            cgdd_efc = crop.cgdd_for_efc
            cgdd_term = crop.cgdd_for_termination
            ncgdd_dev = crop.ncgdd_for_dev
            ncgdd_late_season = crop.ncgdd_for_late_season

            # Reset cutting flag (this probably doesn't need to happen every time step)
            foo.cutting = 0

            # Special case for ALFALFA hay (typical, beef or dairy)  ' 4/09
            if ((crop.class_number == 1 and data.crop_one_flag) or crop.class_number == 2 or crop.class_number == 3 or
                    (crop.class_number >= 4 and crop.curve_name.upper() == "ALFALFA 1ST CYCLE")):
                # termination for first cycle for alfalfa is in EFC cumGDD
                cgdd_term = crop.cgdd_for_efc
                # termination for all other alfalfa cycles is stored in termination cumGDD.
                if foo.cycle > 1:
                    # 'term' cumGDD is for second cycles
                    cgdd_efc = crop.cgdd_for_termination
                    cgdd_term = crop.cgdd_for_termination

            if cgdd_in_season < cgdd_efc:
                foo.n_cgdd = cgdd_in_season / cgdd_efc
                if foo.n_cgdd * 100 <= ncgdd_dev:
                    foo.kc_bas = kc_ini
                else:
                    foo.kc_bas = kc_ini + (foo.n_cgdd - ncgdd_dev / 100) * (kc_mid - kc_ini) / (1 - ncgdd_dev / 100)
                if debug_flag:
                    logging.debug('kc_daily(): kcb %.6f  ncumGDD %d' % (foo.kc_bas, foo.n_cgdd))
                    logging.debug('kc_daily(): cgdd_in_season %d  cgdd_efc %.6f' % (cgdd_in_season, cgdd_efc))
                    logging.debug('kc_daily(): cumGDD %.6f  cgdd_at_planting %.6f' % (foo.cgdd, foo.cgdd_at_planting))
            else:
                foo.n_cgdd = cgdd_in_season / cgdd_efc  # use ratio of cumGDD for EFC
                if foo.n_cgdd < ncgdd_late_season / 100:
                    foo.kc_bas = kc_mid
                elif cgdd_in_season < cgdd_term:  # function is same as for < EFC
                    # keep constant in mid-term
                    # Hold kc equal to Kc mid until either cumGDD terminations exceeded or killing frost
                    foo.kc_bas = kc_mid + (kc_end - kc_mid) / (cgdd_term / cgdd_efc - ncgdd_late_season / 100) * (
                            foo.n_cgdd - ncgdd_late_season / 100)
                    if debug_flag:
                        logging.debug('kc_daily(): kc_bas %.6f  kc_curve_num %d' % (foo.kc_bas, kc_curve_num))
                else:
                    # End of season by exceeding cumGDD for termination.
                    # Note that for cumGDD based crops,
                    #   there is no extension past computed end
                    foo.in_season = False
                    logging.debug('kc_daily(): curve_type 1  in_season %d' % foo.in_season)

                    if crop.cutting_crop:
                        # (three curves for cycles, two cumGDD's for first and other cycles)
                        foo.cutting = 1

                        # review code is commented out
                        # Remember gu, cutting and frost dates for alfalfa crops for review
                        # foo.cutting[foo.cycle] = foo_day.doy

                        # Increment and reset for next cycle
                        foo.cycle += 1
                        foo.in_season = True
                        logging.debug('kc_daily(): in_season %d' % foo.in_season)
                        # Set basis for next cycle
                        foo.cgdd_at_planting = foo.cgdd

                        # Following 2 lines added July 13, 2009 by RGA to reset
                        #   alfalfa height to minimum each new cycle
                        #   and to set kcb to initial kcb value for first day following cutting.
                        foo.height = foo.height_min
                        foo.kc_bas = kc_ini
                        if debug_flag:
                            logging.debug('kc_daily(): kc_bas %.6f  cgdd_at_planting %.6f  cutting %d' %
                                          (foo.kc_bas, foo.cgdd_at_planting, foo.cutting))

            # Use this here only to invoke a total length limit
            days_into_season = foo_day.doy - foo.doy_start_cycle + 1
            if days_into_season < 1:
                days_into_season += 365

            # Real value for length constraint (used for spring grain)
            # cumGDD basis has exceeded length constraint.
            if 10 < crop.time_for_harvest < days_into_season:
                # End season
                foo.in_season = False  # This section added Jan. 2007
                logging.debug('kc_daily(): curve_type 1  in_season %d' % foo.in_season)

        # crop.curve_type Case 2
        elif crop.curve_type == 2:
            # Percent of time from PL to EFC for all season
            days_into_season = foo_day.doy - foo.doy_start_cycle + 1
            if days_into_season < 1:
                days_into_season += 365
            # Deal with values of zero or null - added Dec. 29, 2011, rga
            crop.time_for_efc = max(crop.time_for_efc, 1.)
            foo.n_pl_ec = float(days_into_season) / crop.time_for_efc
            npl_ec100 = foo.n_pl_ec * 100

            time_percent_for_dev = crop.time_percent_for_dev
            time_percent_for_late_season = crop.time_percent_for_late_season
            time_percent_for_termination = abs(crop.time_for_harvest)
            if time_percent_for_late_season > time_percent_for_termination:
                time_percent_for_late_season = time_percent_for_termination
            logging.debug('kc_daily(): npl_ec100 %s  time_for_harvest %.6f  abs_time_for_harvest %.6f' %
                          (npl_ec100, crop.time_for_harvest, abs(crop.time_for_harvest)))
            # Notice!: crop.time_for_efc is the days from planting to full effective cover,
            # but crop.time_for_harvest is percent time (ratio between days from planting to harvest and time_for_efc)
            if npl_ec100 <= 100:
                if npl_ec100 <= time_percent_for_dev:
                    foo.kc_bas = kc_ini
                else:
                    foo.kc_bas = kc_ini + (npl_ec100 - time_percent_for_dev) * (kc_mid - kc_ini) / (
                            100 - time_percent_for_dev)

                if debug_flag:
                    logging.debug('kc_daily(): kc_bas %.6f  n_pl_ec %d' % (foo.kc_bas, foo.n_pl_ec))
                    logging.debug(
                        'kc_daily(): days_into_season %d  time_for_EFC %.6f' % (days_into_season, crop.time_for_efc))
            elif npl_ec100 <= time_percent_for_termination:
                if npl_ec100 <= time_percent_for_late_season:
                    foo.kc_bas = kc_mid
                else:
                    foo.kc_bas = kc_mid + (kc_end - kc_mid) / (
                            time_percent_for_termination - time_percent_for_late_season) * (
                                         npl_ec100 - time_percent_for_late_season)
            else:
                # beyond stated end of season
                # ------need provision to extend until frost termination
                #       if indicated for crop -- added Jan. 2007
                if crop.time_for_harvest < -0.5:
                    # negative value is a flag to extend until frost
                    # XXXXXXXXX  Need to set to yesterday's kcb for a standard climate
                    # use yesterday's kcb which should trace back to
                    # last valid day of stated growing season
                    foo.kc_bas = kc_end
                    logging.debug('kc_daily(): kc_bas %.6f' % foo.kc_bas)
                else:
                    foo.in_season = False
                    logging.debug('kc_daily(): curve_type 2  in_season %d' % foo.in_season)

        # crop.curve_type Case 3
        elif crop.curve_type == 3:
            # Percent of time from PL to EFC for before EFC and days after EFC after EFC
            days_into_season = foo_day.doy - foo.doy_start_cycle + 1
            if days_into_season < 1:
                days_into_season += 365

            # Deal with values of zero or null - added Dec. 29, 2011, rga
            crop.time_for_efc = max(crop.time_for_efc, 1.)
            foo.n_pl_ec = float(days_into_season) / crop.time_for_efc
            if foo.n_pl_ec < 1:
                int_pl_ec = min(int(foo.n_pl_ec * 10.), foo.max_lines_in_crop_curve_table - 1)
                foo.kc_bas = (et_cell.crop_coeffs[curve_number].data[int_pl_ec] + (foo.n_pl_ec * 10 - int_pl_ec) *
                              (et_cell.crop_coeffs[curve_number].data[int_pl_ec + 1] -
                               et_cell.crop_coeffs[curve_number].data[int_pl_ec]))
                logging.debug(
                    'kcb_daily(): kc_bas %.6f  n_pl_ec %.6f  max_lines_in_crop_curve_table %d  int_pl_ec %d' %
                    (foo.kc_bas, foo.n_pl_ec, foo.max_lines_in_crop_curve_table, int_pl_ec))
            else:
                DaysafterEFC = days_into_season - crop.time_for_efc

                # In next line, make sure that "System.Math.Abs()" does not
                #   change exact value for time_for_harvest() and that it is
                #   taking absolute value.
                # Use absolute value for time_for_harvest since neg means to
                #   run until frost (Jan. 2007). also changed to <= from <
                if DaysafterEFC <= abs(crop.time_for_harvest):
                    # Start at array index = 11 for 0 days into full cover
                    nDaysafterEFC = float(DaysafterEFC) / 10 + 11
                    int_pl_ec = min(int(nDaysafterEFC), foo.max_lines_in_crop_curve_table - 1)
                    foo.kc_bas = (et_cell.crop_coeffs[curve_number].data[int_pl_ec] + (nDaysafterEFC - int_pl_ec) *
                                  (et_cell.crop_coeffs[curve_number].data[int_pl_ec + 1] -
                                   et_cell.crop_coeffs[curve_number].data[int_pl_ec]))
                    logging.debug('kcb_daily(): kc_bas %.6f  n_pl_ec %.6f  nDaysafterEFC %.6f  int_pl_ec %.6f' %
                                  (foo.kc_bas, foo.n_pl_ec, nDaysafterEFC, int_pl_ec))
                elif crop.time_for_harvest < -0.5:
                    # beyond stated end of season
                    # ------need provision to extend until frost termination
                    #       if indicated for crop -- added Jan. 2007
                    # negative value is a flag to extend until frost -- added Jan. 2007

                    # XXXX need to set to yesterday's standard climate kcb
                    # use yesterday's kcb which should trace back to
                    # last valid day of stated growing season
                    foo.kc_bas = foo.kc_bas_prev
                    logging.debug('kcb_daily(): kc_bas %.6f' % foo.kc_bas)
                else:
                    foo.in_season = False
                    logging.debug('kcb_daily(): curve_type 3  in_season %d' % foo.in_season)

        # crop.curve_type Case 4
        elif crop.curve_type == 4:
            # print('CURVE TYPE 4')
            # Percent of time from PL to end of season
            # Note that type 4 kcb curve uses T30 to estimate GU
            #   and symmetry around July 15 to estimate total season length.
            # print(foo.doy_start_cycle)
            # print(crop.gdd_trigger_doy)
            # Estimate end of season
            if foo.doy_start_cycle < (crop.gdd_trigger_doy + 195):
                # CGM - end_of_season is not used anywhere else?
                # end_of_season = (
                #     .gdd_trigger_doy  + 195 +
                #     .gdd_trigger_doy  + 195 - foo.doy_start_cycle))
                length_of_season = 2 * (crop.gdd_trigger_doy + 195 - foo.doy_start_cycle)
                # print(length_of_season)
                # end_of_season = 196 + (196 - foo.doy_start_cycle)
                # length_of_season = 2 * (196 - foo.doy_start_cycle)
            else:
                logging.error(
                    ('kc_daily.kcb_daily(): Problem with estimated season length, crop_curve_type_4, crop {}.' +
                     ' Check T30 (too low) or PL_GU_Date Negative Offset.').format(crop.class_number))
                sys.exit()
            # Limit growing season length to 366 days
            if length_of_season > 366:
                logging.info('ADJUSTING GROWING SEASON (NOT CENTERING ON JULY 15)')
                length_of_season = 366

            # Put a minimum and maximum length on season for cheat grass (i= 47)
            # Was 38, should have been 42   'corr. Jan 07

            if crop.class_number == 47:
                length_of_season = max(length_of_season, 60)
                if length_of_season > 90:
                    length_of_season = 100

            days_into_season = foo_day.doy - foo.doy_start_cycle
            # changed from 1 to Zero on 4/8/2020
            if days_into_season < 0:
                # print('days_into_season adjustment')
                days_into_season += 365

            foo.n_pl_ec = float(days_into_season) / length_of_season
            # print(foo.n_pl_ec)
            if foo.n_pl_ec <= 1:
                int_pl_ec = min(foo.max_lines_in_crop_curve_table - 1, int(foo.n_pl_ec * 10))
                # et_cell.crop_coeffs[curve_number].data[int_pl_ec]
                foo.kc_bas = (et_cell.crop_coeffs[curve_number].data[int_pl_ec] + (foo.n_pl_ec * 10 - int_pl_ec) *
                              (et_cell.crop_coeffs[curve_number].data[int_pl_ec + 1] -
                               et_cell.crop_coeffs[curve_number].data[int_pl_ec]))
                logging.debug('kcb_daily(): kc_bas %.6f' % foo.kc_bas)
            else:
                # Beyond end of season

                foo.in_season = False
                logging.debug('kcb_daily(): curve_type 4  in_season %d' % foo.in_season)

        # Determine if killing frost to cut short - begin to check after August 1.
        if foo_day.doy > (crop.gdd_trigger_doy + 211):
            # All crops besides covers
            if ((foo_day.tmin < crop.killing_frost_temperature) and
                    (crop.class_number < 44 or crop.class_number > 46) and foo.in_season):
                logging.info("Killing frost for crop %d of %.1f was found on DOY %d of %d" %
                             (crop.class_number, crop.killing_frost_temperature, foo_day.doy, foo_day.year))
                foo.in_season = False
                logging.debug('kcb_daily(): in_season %d' % foo.in_season)

            # DEADBEEF -only purpose of this section appears to be for logging
            # End of year, no killing frost on alfalfa
            elif (((crop.class_number == 2 or crop.class_number == 3) or
                   (crop.class_number > 3 and crop.curve_name.upper() == "ALFALFA 1ST CYCLE")) and
                  foo.in_season and foo_day.month == 12 and foo_day.day == 31):
                logging.info("No killing frost in year %d" % foo_day.year)

    # Sub in winter time kcb if before or after season

    # Kcb for winter time land use
    #   44: Bare soil
    #   45: Mulched soil, including grain stubble
    #   46: Dormant turf/sod (winter time)
    #   Note: set kc_max for winter time (Nov-Mar) and fc outside of this sub.
    # CGM 9/2/2015 - 44-46 are not run first in Python version of ET-Demands
    #   kc_bas_wscc is set in initialize_crop_cycle(), no reason to set it here

    # Save kc_bas_prev prior to CO2 adjustment to avoid double correction
    foo.kc_bas_prev = foo.kc_bas

    if crop.class_number in [44, 45, 46]:
        if crop.class_number == 44:
            foo.kc_bas = 0.1  # was 0.2
            # foo.kc_bas_wscc[1] = foo.kc_bas
        elif crop.class_number == 45:
            foo.kc_bas = 0.1  # was 0.2
            # foo.kc_bas_wscc[2] = foo.kc_bas
        elif crop.class_number == 46:
            foo.kc_bas = 0.1  # was 0.3
            # foo.kc_bas_wscc[3] = foo.kc_bas
        logging.debug('kcb_daily(): kc_bas %.6f' % foo.kc_bas)

        # Save kcb value for use tomorrow in case curve needs to be extended until frost
        # Save kc_bas_prev prior to CO2 adjustment to avoid double correction
        foo.kc_bas_prev = foo.kc_bas

    # Open water evaporation "crops"
    #   55: Open water shallow systems (large ponds, streams)
    #   56: Open water deep systems (lakes, reservoirs)
    #   57: Open water small stock ponds
    #   This section for WATER only

    elif crop.class_number in [55, 56, 57]:
        if crop.class_number == 55:
            if data.refet['type'] == 'eto':
                # Note that these values are substantially different from FAO56
                foo.kc_bas = 1.05
            elif data.refet['type'] == 'etr':
                # etr kc_bas is eto_kc_bas / 1.2 [1.05/1.2 = 0.875]
                foo.kc_bas = 0.875
        elif crop.class_number == 56:
            # This is a place holder, since an aerodynamic function is used
            # foo.kc_bas = 0.3
            print("no need to cal open water et")
        elif crop.class_number == 57:
            if data.refet['type'] == 'eto':
                foo.kc_bas = 0.85
            elif data.refet['type'] == 'etr':
                foo.kc_bas = 0.7
        logging.debug('kcb_daily(): kc_bas %.6f' % foo.kc_bas)

        # Water has only 'kcb'

        foo.kc_act = foo.kc_bas
        foo.kc_pot = foo.kc_bas

        # ETr changed to ETref 12/26/2007
        foo.etc_act = foo.kc_act * foo_day.etref
        foo.etc_pot = foo.kc_pot * foo_day.etref
        foo.etc_bas = foo.kc_bas * foo_day.etref

        # Save kcb value for use tomorrow in case curve needs to be extended until frost
        # Save kc_bas_prev prior to CO2 adjustment to avoid double correction
        foo.kc_bas_prev = foo.kc_bas

    # Adjustment to kcb moved here 2/21/08 to catch when during growing season
    # Limit crop height for numerical stability

    foo.height = max(foo.height, 0.05)

    # RHmin and U2 are computed in ETCell.set_weather_data()
    # Allen 3/26/08

    if data.refet['type'] == 'eto':
        # ******'12/26/07
        foo.kc_bas = (foo.kc_bas + (0.04 * (foo_day.u2 - 2) - 0.004 * (foo_day.rh_min - 45)) * (foo.height / 3) ** 0.3)
        logging.debug('kcb_daily(): kcb %.6f  u2 %.6f  rh_min %.6f  height %.6f' %
                      (foo.kc_bas, foo_day.u2, foo_day.rh_min, foo.height))

    # ETr basis, therefore, no adjustment to kc
    elif data.refet['type'] == 'etr':
        pass
