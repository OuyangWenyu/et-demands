"""compute_crop_et.py
Function for calculating crop et
Called by crop_cycle.py

"""

import datetime
import logging
import math
import sys
import src.cropet4gages.util as util


def compute_crop_et(data, et_cell, crop, foo, foo_day, debug_flag=False):
    """Crop et computation for every crop in a GAGES-II basin

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
        See comments in code

        """

    # Don't compute cropET for open water
    # open_water_evap() was called in kcb_daily()
    if crop.class_number in [55, 56, 57]:
        return

    # Maximum Kc when soil is wet.  For grass reference, kc_max = 1.2 plus climatic adj.
    # For alfalfa reference, kc_max = 1.0, with no climatic adj.
    # kc_max is set to less than 1.0 during winter to account for effects of cold soil.

    # ETo basis:  Switched over to this 12/2007  # Allen and Huntington
    # Note that U2 and RHmin were disabled when KcETr code was converted to ETr basis
    #   these have been reactivated 12/2007 by Allen, based on daily wind and TDew
    # RHmin and U2 are computed in ETCell.set_weather_data()

    # Limit height for numerical stability
    foo.height = max(0.05, foo.height)
    if data.refet['type'] == 'eto':
        kc_max = ((0.04 * (foo_day.u2 - 2) - 0.004 * (foo_day.rh_min - 45)) * (foo.height / 3) ** 0.3)
        if crop.kc_max > 0.3:
            kc_max += crop.kc_max
        else:
            kc_max += 1.2
    elif data.refet['type'] == 'etr':  # edited by Allen, 6/8/09 to use kc_max from file if given
        if crop.kc_max > 0.3:
            kc_max = crop.kc_max
        else:
            kc_max = 1.0
    else:
        sys.exit()

    # Kc_max and foo.fc for wintertime land use (Nov-Mar)
    # wscc = 1 bare, 2 mulch, 3 sod
    wscc = crop.winter_surface_cover_class

    # Assume that winter time is constrained to Nov-March in northern hemisphere
    # Also set up kc_max for non-growing seasons for other crops
    # Kc_max for wintertime land use (Nov-Mar)for non-growing season crops
    if util.is_winter(et_cell, foo_day):
        if crop.class_number not in [44, 45, 46]:
            # Note that these are ETr based.  (Allen 12/2007)
            # Multiply by 1.2 (plus adj?) for ETo base
            if wscc == 1:
                # bare soil
                # foo.fc is calculated below
                if data.refet['type'] == 'eto':
                    kc_max = 1.1
                elif data.refet['type'] == 'etr':
                    kc_max = 0.9
            elif wscc == 2:
                # Mulched soil, including grain stubble
                if data.refet['type'] == 'eto':
                    kc_max = 1.0
                elif data.refet['type'] == 'etr':
                    kc_max = 0.85
            elif wscc == 3:
                # Dormant turf/sod (winter time)
                if data.refet['type'] == 'eto':
                    kc_max = 0.95
                elif data.refet['type'] == 'etr':
                    kc_max = 0.8
        elif crop.class_number == 44:
            # Bare soil
            # Less soil heat in winter.
            if data.refet['type'] == 'eto':
                # For ETo  (Allen 12/2007)
                kc_max = 1.1
            elif data.refet['type'] == 'etr':
                # For ETr (Allen 3/2008)
                kc_max = 0.9
            foo.fc = 0.0
        elif crop.class_number == 45:
            # Mulched soil, including grain stubble
            if data.refet['type'] == 'eto':
                # For ETo (0.85 * 1.2)  (Allen 12/2007)
                kc_max = 1.0
            elif data.refet['type'] == 'etr':
                # For ETr (Allen 3/2008)
                kc_max = 0.85
            foo.fc = 0.4
        elif crop.class_number == 46:
            # Dormant turf/sod (winter time)
            if data.refet['type'] == 'eto':
                # For ETo (0.8 * 1.2)  (Allen 12/2007)
                kc_max = 0.95
            elif data.refet['type'] == 'etr':
                # For ETr (Allen 3/2008)
                kc_max = 0.8
            # Was 0.6
            foo.fc = 0.7

    # added 2/21/08 to make sure that a winter cover class is used if during non-growing season
    # override Kc_bas assigned from kcb_daily() if non-growing season and not water
    if not foo.in_season and (crop.class_number < 55 or crop.class_number > 57):
        logging.debug(
            'compute_crop_et(): kc_bas %.6f  kc_bas_wscc %.6f  wscc %.6f' % (foo.kc_bas, foo.kc_bas_wscc[wscc], wscc))
        # Set higher dormant kc min for warm season turfgrass (Crop 87); added 5/1/2020
        if crop.class_number in [87]:
            foo.kc_bas = 0.25
        else:
            foo.kc_bas = foo.kc_bas_wscc[wscc]

    # limit kc_max to at least Kc_bas + .05
    kc_max = max(kc_max, foo.kc_bas + 0.05)

    # kc_min is minimum evaporation for 0 ground cover under dry soil surface
    # but with diffusive evaporation.
    # kc_min is used to estimate fraction of ground cover for crops.
    # Set kc_min to 0.1 for all vegetation covers (crops and natural)
    # Kc_bas will be reduced for all surfaces not irrigated when stressed, even during winter.

    # Use same value for both ETr or ETo bases.
    foo.kc_min = 0.1

    # Estimate height of vegetation for estimating fraction of ground cover
    #   for evaporation and fraction of ground covered by vegetation
    if crop.class_number not in [44, 45, 46]:
        if kc_max <= foo.kc_min:
            kc_max = foo.kc_min + 0.001

    if debug_flag:
        logging.debug('compute_crop_et(): kc_max %.6f  kc_min %.6f  kc_bas %.6f  in_season %d' % (
            kc_max, foo.kc_min, foo.kc_bas, foo.in_season))

    # just set kc_act and kc_pot as kc_bas (since here what I am using is Kc method)
    foo.kc_act = foo.kc_bas
    foo.kc_pot = foo.kc_bas

    # ETref is defined (to ETo or ETr) in CropCycle sub #'Allen 12/26/2007
    foo.etc_act = foo.kc_act * foo_day.etref
    foo.etc_pot = foo.kc_pot * foo_day.etref
    foo.etc_bas = foo.kc_bas * foo_day.etref
    if debug_flag:
        logging.debug(
            'compute_crop_et(): kc_bas %.6f  kc_pot %.6f  kc_act %.6f' % (foo.kc_bas, foo.kc_pot, foo.kc_act))
        logging.debug(
            'compute_crop_et(): etc_bas %.6f  etc_pot %.6f  etc_act %.6f' % (foo.etc_bas, foo.etc_pot, foo.etc_act))

