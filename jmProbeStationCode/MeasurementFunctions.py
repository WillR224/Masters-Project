#!/usr/bin/python
# MeasurementFunctions.py -- contains classes for running IV and CV tests
# Updated: 05/03/2021
# Contributing: Matt Basso (University of Toronto), Tim Knight (University of Toronto), Will George (University of Birmingham)

import sys, os, time
from Plots import IVTimePlot as TimePlot
from Plots import TwoIVPlotWindow as MD8TimePlot
from Plots import IVPlotWindow
from Plots import CVPlotWindow

from colorama import Fore, Style

def WARNING(message):
    print(Fore.YELLOW + '[WARNING]' + Style.RESET_ALL + '$ {}'.format(message))

def ERROR(message):
    print(Fore.RED + '[ERROR]' + Style.RESET_ALL + '$ {}'.format(message))

def raiseError(message):
    ERROR(message)
    ERROR('Finished with error.')
    sys.exit(1)
    
def STATUS(message, success):
    if success:
        print(Fore.GREEN + '[STATUS]' + Style.RESET_ALL + '$ {}'.format(message))
    else:
        print(Fore.RED + '[STATUS]' + Style.RESET_ALL + '$ {}'.format(message))


class HitCompliance(Exception):
    ''' Class to define custom exception. ''' 
    pass


def measureIV_PS(ps,save_path,Vstep,Vinitial,Vfinal,Imax,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time):
    ''' IV test using single power supply to apply voltage and measure current. '''

    #################################################################################################################################
    # Define the number of times we have to fail our compliance check to raise HitCompliance
    # The code will ramp down when the current number of consecutive failed compliance checks (COMPLIANCE_CHECK) equals the max (COMPLIANCE_CHECK_MAX)
    # VSTEP_PER_CHECK := Voltage step size before a compliance check is made (during ramping, assuming --fullStep = False)
    # WAIT_TIME_PER_CHECK := If the first compliance check fails, how long in seconds to wait before performing another one
    # Note, these variables are not used until later in the code, but are defined at the top for convenience
    COMPLIANCE_CHECK_MAX = 5
    COMPLIANCE_CHECK = 0
    # VSTEP_PER_CHECK should probably be a multiple of 0.1
    VSTEP_PER_CHECK = 2.5
    WAIT_TIME_FOR_CHECK = 1.0
    current_check = 0
    #################################################################################################################################

    dyn_rest_time = None  #turn off dyn rest time logic
    dyn_rest_dV = 10.0
    dyn_rest_max = 1.0

    sht21 = False

    sht = 0
    if(sht21):
        try:
            sht = 0 #SHT_monitor()
        except:
            sht = 0

    # Check if initial voltage and power supply voltage match
    Vinitial_CHECK = float(ps.readVoltageAndCurrent()[0])
    if Vinitial != (int)(Vinitial_CHECK):
            raiseError('--Vinitial does not match starting power supply voltage: {0} V =/= {1} V'.format(str(Vinitial), str(Vinitial_CHECK)))
    print('--Vinitial correctly matches starting power supply voltage...')

    # Generate the save file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time PS Voltage(V) PS Current(A)\n')
    print('{0} created successfully...'.format(save_path))

    # Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = IVPlotWindow()
    plot.open()

    print('Opening time plot window...')
    timeplot = TimePlot()

    # Perform the measurement
    print('Beginning measurement...')

    # Take dV to equal Vstep is full_step is specified
    # Else set dV (the increment the power supply is stepped in) to +/-0.1 V
    if full_step:
        dV = Vstep
    else:
        dV = 0.1 if Vstep > 0 else -0.1

    N_small_steps = int(abs(Vstep / dV))
    N_big_steps = int(abs((Vfinal - Vinitial) / Vstep))
    Vcurrent = Vinitial

    # Get the j values (index in our range(N_small_steps) loop below) where we want to perform compliance checking
    j_CHECK = int(abs(VSTEP_PER_CHECK / dV))

    # In case dV is less than 1 (e.g., we're using fullStep = -10 V and VSTEP_PER_CHECK = 5 V), check every step
    if j_CHECK < 1:
        j_CHECK = 1

    # Compliance checking function
    def checkCompliance():

        nonlocal COMPLIANCE_CHECK

        # If in compliance, increment our compliance check and stop ramping
        if ps.inCompliance():
            COMPLIANCE_CHECK += 1
            WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))

            while True:

                # Wait before checking compliance again
                print('Waiting {0} s before checking compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                time.sleep(WAIT_TIME_FOR_CHECK)

                # If we're in compliance, increment our check
                # Else, break out of the loop to start ramping again and reset our compliance check
                if ps.inCompliance():
                    COMPLIANCE_CHECK += 1
                    WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))
                else:
                    print('Compliance check passed -- resetting check count.')
                    COMPLIANCE_CHECK = 0
                    break

                # If we reach our max compliance check, throw an exception
                if COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                    raise HitCompliance

    ps.controlAverage('on')

    try:

        # Loop though our big voltage steps
        for i in range(N_big_steps + 1):

            print('Waiting {0} s...'.format(str(rest_time)))
            time.sleep(rest_time)
            print('Making a measurement...')
            voltage, current = ps.readVoltageAndCurrent()

            if float(current) > Imax:
                current_check = 1
                Vfinal = Vcurrent
                break

            if dyn_rest_time is not None:
                dyn_rest_attempt = 0
                while True:
                    if dyn_rest_attempt <= dyn_rest_max:
                        if not abs(Vcurrent - float(voltage)) < dyn_rest_dV:
                            WARNING('Voltage difference between set and measured values is not less than %s V, waiting an extra %s s: Vset = %s V, Vmeas = %s V' % (dyn_rest_dV, dyn_rest_time, Vcurrent, voltage))
                            time.sleep(dyn_rest_time)
                            checkCompliance()
                            voltage, current = ps.readVoltageAndCurrent()
                            dyn_rest_attempt += 1
                        else:
                            break
                    else:
                        WARNING('Number of dynamic rest time attempts exceeds maximum allowed (%s), keeping last measurement and continuing.' % dyn_rest_max)
                        break
            date_time = time.strftime('%Y/%m/%d-%H:%M:%S')

            temperature = '-999'
            humidity    = '-999'
            if(sht):
                temperature = sht.read_temp().strip()
                humidity = sht.read_humi().strip()
                while temperature == '' or humidity == '':
                    sht.clearHandles()
                    temperature = sht.read_temp().strip()
                    humidity = sht.read_humi().strip()

            measurement = [date_time, voltage, current]
            data.write(' '.join(measurement) + '\n')

            long_measurement = [date_time, voltage, current, temperature, humidity]
            plot.update(long_measurement)
            timeplot.update(long_measurement)
            print('At {0}: V = {1} V, I = {2} A, T = {3} C, RH = {4}%.'.format(*long_measurement))

            # If we are on our last big step, we can break as we no longer need to ramp
            if i == N_big_steps:
                break

            ps.controlAverage('off')

            print('Ramping from {0} V to {1} V...'.format(str(Vcurrent), str(Vcurrent + Vstep)))
            for j in range(N_small_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)

                # If we have stepped through a voltage of VSTEP_PER_CHECK, check the compliance
                if ((j+1) % j_CHECK == 0):
                    checkCompliance()

            ps.controlAverage('on')

    # Catch our compliance exception
    except HitCompliance:

        ERROR('Failed compliance check {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK_MAX)))
        print('Saving IV plots...')
        plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()
        timeplot.close()

        # Perform concluding tasks and exit the program if --killOnHitComp = True
        if kill_on_hit_comp:
            print('Concluding run...')
            print('Closing power supply serial port...')
            ps.shutdown()
            print('Run finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            STATUS('Finished with error.', False)
            sys.exit(1)

        else:

            # Reset dV to +0.5 for the purposes of ramping down
            if Vcurrent > 0:
                dV = -0.5
            elif Vcurrent < 0:
                dV = 0.5

            # Calculate the number of voltage steps
            N_rampDown_steps = int(abs(Vcurrent) / abs(dV))

            print('Waiting 5 s prior to ramping down...')
            time.sleep(5)
            print('Ramping from {0} V to 0 V...'.format(str(Vcurrent)))

            ps.controlAverage('off')
            for i in range(N_rampDown_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)

            print('Ramp down finished.')
            print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))

        return

    except Exception as e:

        print('***ERROR*** something has gone wrong - error message to follow...')

        print('Saving IV plots...')
        plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()
        timeplot.close()
        ps.shutdown()
        STATUS('Finished with error.', False)
        print('Python error message below:')
        raise(e)

    print('Measurement finished.')

    print('Saving IV plots...')
    plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    timeplot.close()

    # Ramp down from Vfinal to 0 V
    if ramp_down and Vfinal != 0 and Vcurrent != 0:

        if Vcurrent > 0:
            dV = -0.5
        elif Vcurrent < 0:
            dV = 0.5

        N_rampDown_steps = int((abs(Vfinal) - 1) / abs(dV))
        print('Waiting 5 s prior to ramping down...')
        time.sleep(5)
        print('Ramping from {0} V to -1 V...'.format(str(Vcurrent)))

        ps.controlAverage('off')
        for i in range(0, N_rampDown_steps):
            Vcurrent += dV
            ps.setVoltage(Vcurrent)
            time.sleep(0.02)

        print('Ramping up from -1 V to 0 V...')

        if Vcurrent > 0:
            dV = -0.1
        elif Vcurrent < 0:
            dV = 0.1
        for j in range(0,10):
            Vcurrent += dV
            ps.setVoltage(Vcurrent)
            time.sleep(0.1)

    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    return current_check


def measureIV_SMU(ps,am,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time):
    ''' IV test using two power supplies: ps is ramped to a fixed voltage for the test and ramped down after again, am performs IV sweep and ramps down after. '''

    # ps_Vinitial should be 0
    # am_Vinitial is measurement starting V --> need to set am_Vcurrent = 0
    am_Vcurrent = 0.

    #########################################################################################
    # Define the number of times we have to fail our compliance check to raise HitCompliance
    COMPLIANCE_CHECK_MAX = 5
    COMPLIANCE_CHECK = 0
    SMU_COMPLIANCE_CHECK = 0
    VSTEP_PER_CHECK = 0.5 # should probably be a multiple of 0.1
    WAIT_TIME_FOR_CHECK = 1.0
    #########################################################################################

    sht21 = False
    sht = 0

    # Check if initial voltage and power supply voltage match
    Vinitial_CHECK = float(ps.readVoltageAndCurrent()[0])
    if abs(ps_Vinitial- Vinitial_CHECK)>0.01:
            raiseError('--ps_Vinitial does not match starting power supply voltage: {0} V =/= {1} V'.format(str(ps_Vinitial), str(Vinitial_CHECK)))
    print('--ps_Vinitial correctly matches starting power supply voltage...')

    data = open(save_path, 'a')
    data.write('#Date-Time AM Voltage(V) AM Current(A) \n')
    print('{0} created successfully...'.format(save_path))

    print('Opening plot window...')
    plot = IVPlotWindow()
    plot.open()
    print('Opening time plot window...')
    timeplot = TimePlot()
    print('Finished with setup.')

    # Take dV to equal Vstep is full_step is specified
    if full_step:
        ps_dV = ps_Vstep
    else:
        if ps_Vstep > 0:
            ps_dV = 0.1
        else:
            ps_dV = -0.1

    # Get how many dV steps are in our voltage step size
    ps_N_small_steps = int(abs(ps_Vstep/ps_dV))
    # Get how many steps sizes are in our initial to final voltage range
    ps_N_big_steps = int(abs((ps_Vfinal - ps_Vinitial)/ps_Vstep))
    ps_Vcurrent = ps_Vinitial

    # Get the j values (index in our range(N_small_steps) loop below) where we want to perform compliance checking
    j_CHECK = int(abs(VSTEP_PER_CHECK / ps_dV))
    if j_CHECK < 1:
        j_CHECK = 1

    # Compliance checking function
    def checkCompliance():

        nonlocal COMPLIANCE_CHECK

        if ps.inCompliance():
            COMPLIANCE_CHECK += 1
            WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))

            while True:
                print('Waiting {0} s before checking compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                time.sleep(WAIT_TIME_FOR_CHECK)

                if ps.inCompliance():
                    COMPLIANCE_CHECK += 1
                    WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))
                else:
                    print('Compliance check passed -- resetting check count.')
                    COMPLIANCE_CHECK = 0
                    break

                if COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                    raise HitCompliance


    #Ramping HV PS
    try:

        for i in range(ps_N_big_steps + 1):

            print('Waiting {0} s...'.format(str(rest_time)))
            time.sleep(rest_time)

            voltage, current = ps.readVoltageAndCurrent()
            if i == ps_N_big_steps:
                break

            ps.controlAverage('off')

            voltage_low_check,current_low_check = am.readVoltageAndCurrent()

            print('Ramping from {0} V to {1} V...'.format(str(ps_Vcurrent), str(ps_Vcurrent + ps_Vstep)))
            for j in range(ps_N_small_steps):
                ps_Vcurrent += ps_dV
                ps.setVoltage(ps_Vcurrent)
                time.sleep(0.2)

                if ((j+1) % j_CHECK == 0):
                    checkCompliance()

            ps.controlAverage('on')

    except HitCompliance:

        ERROR('Failed compliance check {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK_MAX)))
        print('Saving IV plots...')
        plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()
        timeplot.close()

        if kill_on_hit_compliance:
            print('Closing power supply serial port...')
            ps.shutdown()
            print('Closing {0}...'.format(save_path))
            print('Run finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            STATUS('Finished with error.', False)
            sys.exit(1)

        else:

            if ps_Vcurrent > 0:
                ps_dV = -0.5
            else:
                ps_dV = 0.5

            ps_N_rampDown_steps = int(abs(ps_Vcurrent) / abs(ps_dV))

            print('Waiting 5 s prior to ramping down...')
            time.sleep(5)
            print('Ramping from {0} V to 0 V...'.format(str(ps_Vcurrent)))

            am.controlAverage('off')
            ps.controlAverage('off')

            for i in range(ps_N_rampDown_steps):
                ps_Vcurrent += ps_dV
                ps.setVoltage(ps_Vcurrent)
                time.sleep(0.02)

            print('PS ramp down finished.')
            print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))

        return

    # Compliance checking function for picoammeter
    def smu_checkCompliance():

        nonlocal SMU_COMPLIANCE_CHECK

        # If in compliance, increment our compliance check and stop ramping
        if am.inCompliance():
            SMU_COMPLIANCE_CHECK += 1
            WARNING('Picoammeter compliance check failed {0} consecutive time(s).'.format(str(SMU_COMPLIANCE_CHECK)))

            while True:
                print('Waiting {0} s before checking picoammeter compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                time.sleep(WAIT_TIME_FOR_CHECK)

                if am.inCompliance():
                    SMU_COMPLIANCE_CHECK += 1
                    WARNING('SMU compliance check failed {0} consecutive time(s).'.format(str(SMU_COMPLIANCE_CHECK)))
                else:
                    print('Picoammeter compliance check passed -- resetting check count.')
                    SMU_COMPLIANCE_CHECK = 0
                    break

                # If we reach our max compliance check, throw an exception
                if SMU_COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                    raise HitCompliance

    j_CHECK_SMU = 1

    ## SMU RAMPING
    if(am_Vinitial != 0):

        if am_Vinitial > am_Vcurrent:
            am_dV = 0.1
        else:
            am_dV = -0.1
        am_N_ramp_up_steps = int(abs(am_Vinitial - am_Vcurrent)/abs(am_dV))

        j_CHECK_SMU = int(abs(VSTEP_PER_CHECK / am_dV))
        if j_CHECK_SMU < 1:
            j_CHECK_SMU = 1

        am.controlAverage('off')
        print('Ramping picoammeter from {0} V to {1} V...'.format(str(am_Vcurrent), str(am_Vinitial)))

        try:

            for j in range(am_N_ramp_up_steps):
                am_Vcurrent += am_dV
                am.setVoltage(am_Vcurrent)
                time.sleep(0.5)
                if ((j+1) % j_CHECK_SMU == 0):
                    smu_checkCompliance()
            am.controlAverage('on')

        except HitCompliance:

            ERROR('Picoammeter failed compliance check {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK_MAX)))
            print('Closing {0}...'.format(save_path))
            data.close()
            plot.close()
            timeplot.close()

            if kill_on_hit_compliance:
                print('Closing power supply serial port...')
                ps.shutdown()
                am.shutdown()
                print('Closing {0}...'.format(save_path))
                print('Run finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
                STATUS('Finished with error.', False)
                sys.exit(1)

            else:

                if ps_Vcurrent > 0:
                    ps_dV = -0.5
                else:
                    ps_dV = 0.5

                ps_N_rampDown_steps = int(abs(ps_Vcurrent) / abs(ps_dV))

                print('Waiting 5 s prior to ramping down...')
                time.sleep(5)
                print('Ramping PS from {0} V to 0 V...'.format(str(ps_Vcurrent)))

                am.controlAverage('off')
                ps.controlAverage('off')

                for i in range(ps_N_rampDown_steps):
                    ps_Vcurrent += ps_dV
                    ps.setVoltage(ps_Vcurrent)
                    time.sleep(0.02)
                print('PS ramp down finished.')

                if am_Vcurrent > 0:
                    am_dV = -0.5
                else:
                    am_dV = 0.5
                am_N_rampDown_steps = int(abs(am_Vcurrent) / abs(am_dV))

                print('Ramping picoammeter from {0} V to 0 V...'.format(str(am_Vcurrent)))

                for i in range(am_N_rampDown_steps):
                    am_Vcurrent += am_dV
                    am.setVoltage(am_Vcurrent)
                    time.sleep(0.2)

                print('Picoammeter ramp down finished.')

            print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            return

    ### end SMU ramp up ###

    ps.controlAverage('on')
    am.controlAverage('on')

    ###
    # BEGIN MEASUREMENT
    ###

    if am_Vstep > 0:
        am_dV = 0.1
    else:
        am_dV = -0.1
    am_N_small_steps = int(abs(am_Vstep/am_dV))
    am_N_big_steps = int(abs((am_Vfinal - am_Vinitial)/am_Vstep))

    print('Waiting {} s before making first measurement.'.format(first_point_rest_time))
    time.sleep(first_point_rest_time)
    try:
        for i in range(am_N_big_steps + 1):
            time.sleep(rest_time)
            voltage_low,current_low = am.readVoltageAndCurrent()
            date_time = time.strftime('%Y/%m/%d-%H:%M:%S')

            measurement = [date_time,voltage_low,current_low]
            data.write(' '.join(measurement) + '\n')
            print('V = '+voltage_low+', I = '+current_low)

            temperature = '-999'
            humidity    = '-999'
            long_measurement = [date_time, voltage_low, current_low, temperature, humidity]
            plot.update(long_measurement)
            timeplot.update(long_measurement)

            if i == am_N_big_steps:
                break

            am.controlAverage('off')

            for j in range(am_N_small_steps):
                am_Vcurrent += am_dV
                print('Ramping SMU to '+"{:.2f}".format(am_Vcurrent))
                am.setVoltage(am_Vcurrent)
                time.sleep(0.02)

                if ((j+1) % j_CHECK_SMU == 0):
                    smu_checkCompliance()

            am.controlAverage('on')

    except HitCompliance:

        if kill_on_hit_compliance:
            ps.shutdown()
            data.close()
            sys.exit(1)

        else:

            if am_Vcurrent > 0:
                am_dV = -0.5
            elif am_Vcurrent < 0:
                am_dV = 0.5

            am_N_rampDown_steps = int(abs(am_Vfinal)/abs(am_dV))
            time.sleep(5)
            am.controlAverage('off')

            for i in range(0, am_N_rampDown_steps):
                am_Vcurrent += am_dV
                am.setVoltage(am_Vcurrent)
                time.sleep(0.02)

            am.controlAverage('on')
            print('SMU ramp down finished.')

            if ps_Vcurrent > 0:
                ps_dV = -0.5
            elif ps_Vcurrent < 0:
                ps_dV = 0.5

            ps_N_rampDown_steps = int(abs(ps_Vcurrent)/abs(ps_dV))
            time.sleep(5)

            ps.controlAverage('off')
            for i in range(ps_N_rampDown_steps):
                ps_Vcurrent += ps_dV
                ps.setVoltage(ps_Vcurrent)
                time.sleep(0.02)
            ps.controlAverage('on')
            data.close()

        print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
        return

    print('Measurement finished.')

    print('Saving IV plots...')
    plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    timeplot.close()

    if ramp_down and am_Vfinal != 0:

        if am_Vcurrent > 0:
            am_dV = -0.5
        elif am_Vcurrent < 0:
            am_dV = 0.5

        am_N_rampDown_steps = int(abs(am_Vfinal)/abs(am_dV))

        time.sleep(5)

        am.controlAverage('off')
        for i in range(0, am_N_rampDown_steps):
            am_Vcurrent += am_dV
            am.setVoltage(am_Vcurrent)
            time.sleep(0.02)

        print('SMU ramp down finished.')

    if ramp_down and ps_Vfinal != 0:

        if ps_Vcurrent > 0:
            ps_dV = -0.5
        elif ps_Vcurrent < 0:
            ps_dV = 0.5
        ps_N_rampDown_steps = int(abs(ps_Vfinal) / abs(ps_dV))

        print('Waiting 5 s prior to ramping down...')
        time.sleep(5)
        print('Ramping from {0} V to 0 V...'.format(str(ps_Vcurrent)))

        ps.controlAverage('off')
        for i in range(0, ps_N_rampDown_steps):
            ps_Vcurrent += ps_dV
            ps.setVoltage(ps_Vcurrent)
            time.sleep(0.02)

        print('PS ramp down finished.')

    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))


def measureIV_MD8(ps,am,save_path,Vstep,Vinitial,Vfinal,Imax,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time):
    ''' IV test using two power supplies: ps performs IV sweep and measures current, am does not apply any voltage and simply measures the current. '''


    #################################################################################################################################
    # Define the number of times we have to fail our compliance check to raise HitCompliance
    # The code will ramp down when the current number of consecutive failed compliance checks (COMPLIANCE_CHECK) equals the max (COMPLIANCE_CHECK_MAX)
    # VSTEP_PER_CHECK := Voltage step size before a compliance check is made (during ramping, assuming --fullStep = False)
    # WAIT_TIME_PER_CHECK := If the first compliance check fails, how long in seconds to wait before performing another one
    # Note, these variables are not used until later in the code, but are defined at the top for convenience
    COMPLIANCE_CHECK_MAX = 5
    COMPLIANCE_CHECK = 0
    # VSTEP_PER_CHECK should probably be a multiple of 0.1
    VSTEP_PER_CHECK = 2.5
    WAIT_TIME_FOR_CHECK = 1.0
    current_check = 0
    #################################################################################################################################

    # Check if Vstep is multiple of VSTEP_PER_CHECK
    #if not (Vstep % VSTEP_PER_CHECK == 0):
    #    raiseError('abs(--Vstep) is not a multiple of {0} V: abs(--Vstep) = {1} V'.format(str(VSTEP_PER_CHECK), str(abs(Vstep))))

    dyn_rest_time = None  #turn off dyn rest time logic
    dyn_rest_dV = 10.0
    dyn_rest_max = 1.0

    sht21 = False

    sht = 0
    if(sht21):
        try:
            sht = 0 #SHT_monitor()
        except:
            sht = 0

    # Check if initial voltage and power supply voltage match
    Vinitial_CHECK = float(ps.readVoltageAndCurrent()[0])
    if Vinitial != Vinitial_CHECK:
            raiseError('--Vinitial does not match starting power supply voltage: {0} V =/= {1} V'.format(str(Vinitial), str(Vinitial_CHECK)))
    print('--Vinitial correctly matches starting power supply voltage...')

    # Generate the save file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time PS Voltage(V) AM Current(A) PS Current(A)\n')
    print('{0} created successfully...'.format(save_path))

    # Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = IVPlotWindow()
    plot.open()

    print('Opening time plot window...')
    timeplot = MD8TimePlot()

    # Perform the measurement
    print('Beginning measurement...')

    # Take dV to equal Vstep is full_step is specified
    # Else we'll set dV (the increment the power supply is stepped in) to +/-0.1 V, like what Bianca used for the IV code
    if full_step:
        dV = Vstep
    else:
        dV = 0.1 if Vstep > 0 else -0.1

    N_small_steps = int(abs(Vstep / dV))
    N_big_steps = int(abs((Vfinal - Vinitial) / Vstep))
    Vcurrent = Vinitial

    # Get the j values (index in our range(N_small_steps) loop below) where we want to perform compliance checking
    j_CHECK = int(abs(VSTEP_PER_CHECK / dV))

    # In case dV is less than 1 (e.g., we're using fullStep = -10 V and VSTEP_PER_CHECK = 5 V), check every step
    if j_CHECK < 1:
        j_CHECK = 1

    # Compliance checking function
    def checkCompliance():

        nonlocal COMPLIANCE_CHECK

        # If in compliance, increment our compliance check and stop ramping
        if ps.inCompliance():
            COMPLIANCE_CHECK += 1
            WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))

            while True:

                # Wait before checking compliance again
                print('Waiting {0} s before checking compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                time.sleep(WAIT_TIME_FOR_CHECK)

                # If we're in compliance, increment our check
                # Else, break out of the loop to start ramping again and reset our compliance check
                if ps.inCompliance():
                    COMPLIANCE_CHECK += 1
                    WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))
                else:
                    print('Compliance check passed -- resetting check count.')
                    COMPLIANCE_CHECK = 0
                    break

                # If we reach our max compliance check, throw an exception
                if COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                    raise HitCompliance

    ps.controlAverage('on')

    try:

        # Loop though our big voltage steps
        for i in range(N_big_steps + 1):

            print('Waiting {0} s...'.format(str(rest_time)))
            time.sleep(rest_time)
            print('Making a measurement...')
            voltage_high,current_high = ps.readVoltageAndCurrent()
            voltage_low,current_low = am.readVoltageAndCurrent()

            if float(current_high) > Imax:
                current_check = 1
                Vfinal = Vcurrent
                break

            if dyn_rest_time is not None:
                dyn_rest_attempt = 0
                while True:
                    if dyn_rest_attempt <= dyn_rest_max:
                        if not abs(Vcurrent - float(voltage_high)) < dyn_rest_dV:
                            WARNING('Voltage difference between set and measured values is not less than %s V, waiting an extra %s s: Vset = %s V, Vmeas = %s V' % (dyn_rest_dV, dyn_rest_time, Vcurrent, voltage_high))
                            time.sleep(dyn_rest_time)
                            checkCompliance()
                            voltage_high,current_high = ps.readVoltageAndCurrent()
                            voltage_low,current_low = am.readVoltageAndCurrent()
                            dyn_rest_attempt += 1
                        else:
                            break
                    else:
                        WARNING('Number of dynamic rest time attempts exceeds maximum allowed (%s), keeping last measurement and continuing.' % dyn_rest_max)
                        break
            date_time = time.strftime('%Y/%m/%d-%H:%M:%S')

            temperature = '-999'
            humidity    = '-999'
            if(sht):
                temperature = sht.read_temp().strip()
                humidity = sht.read_humi().strip()
                while temperature == '' or humidity == '':
                    sht.clearHandles()
                    temperature = sht.read_temp().strip()
                    humidity = sht.read_humi().strip()

            measurement = [date_time, voltage_high, current_low, current_high]
            data.write(' '.join(measurement) + '\n')

            long_measurement = [date_time, voltage_high, current_low, temperature, humidity]
            plot.update(long_measurement)
            new_meas = [voltage_high, current_low, current_high]
            timeplot.update(new_meas)
            print('At {0}: V_PS = {1} V, I_PS = {2} A, V_AM = {3} V, I_AM = {4} A.'.format(date_time,voltage_high,current_high,voltage_low,current_low))

            # If we are on our last big step, we can break as we no longer need to ramp
            if i == N_big_steps:
                break

            ps.controlAverage('off')

            print('Ramping from {0} V to {1} V...'.format(str(Vcurrent), str(Vcurrent + Vstep)))
            for j in range(N_small_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)

                # If we have stepped through a voltage of VSTEP_PER_CHECK, check the compliance
                if ((j+1) % j_CHECK == 0):
                    checkCompliance()

            ps.controlAverage('on')

    # Catch our compliance exception
    except HitCompliance:

        ERROR('Failed compliance check {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK_MAX)))
        print('Saving IV plots...')
        plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        timeplot.savefig('{0}/MD8_IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()
        timeplot.close()

        # Perform concluding tasks and exit the program if --killOnHitComp = True
        if kill_on_hit_comp:
            print('Concluding run...')
            print('Closing power supply serial port...')
            ps.shutdown()
            am.shutdown()
            print('Run finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            STATUS('Finished with error.', False)
            sys.exit(1)

        else:

            # Reset dV to +0.5 for the purposes of ramping down
            if Vcurrent > 0:
                dV = -0.5
            elif Vcurrent < 0:
                dV = 0.5

            # Calculate the number of voltage steps
            N_rampDown_steps = int(abs(Vcurrent) / abs(dV))

            print('Waiting 5 s prior to ramping down...')
            time.sleep(5)
            print('Ramping from {0} V to 0 V...'.format(str(Vcurrent)))

            ps.controlAverage('off')
            for i in range(N_rampDown_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)

            print('Ramp down finished.')
            print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))

        return

    except Exception as e:

        print('***ERROR*** something has gone wrong - error message to follow...')

        print('Saving IV plots...')
        plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        timeplot.savefig('{0}/MD8_IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()
        timeplot.close()
        ps.shutdown()
        am.shutdown()
        STATUS('Finished with error.', False)
        print('Python error message below:')
        raise(e)

    print('Measurement finished.')

    print('Saving IV plots...')
    plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    timeplot.savefig('{0}/MD8_IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    timeplot.close()

    # Ramp down from Vfinal to 0 V
    if ramp_down and Vfinal != 0 and Vcurrent != 0:

        if Vcurrent > 0:
            dV = -0.5
        elif Vcurrent < 0:
            dV = 0.5

        N_rampDown_steps = int((abs(Vfinal) - 1) / abs(dV))
        print('Waiting 5 s prior to ramping down...')
        time.sleep(5)
        print('Ramping from {0} V to -1 V...'.format(str(Vcurrent)))

        ps.controlAverage('off')
        for i in range(0, N_rampDown_steps):
            Vcurrent += dV
            ps.setVoltage(Vcurrent)
            time.sleep(0.02)

        print('Ramping up from -1 V to 0 V...')

        if Vcurrent > 0:
            dV = -0.1
        elif Vcurrent < 0:
            dV = 0.1
        for j in range(0,10):
            Vcurrent += dV
            ps.setVoltage(Vcurrent)
            time.sleep(0.1)

    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    return current_check



def measureCV(ps,lcr,save_path,Vinitial,Vstart,Vfinal,Vstep_initiate,Vstep_run,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time, lcrFrequencies):
    ''' Peform CV test using power supply, ps, and lcr meter, lcr. '''


    ########################################################################################
    # Define the number of times we have to fail our compliance check to raise HitCompliance
    COMPLIANCE_CHECK_MAX = 5
    COMPLIANCE_CHECK = 0
    WAIT_TIME_FOR_CHECK = 10.0
    ########################################################################################

    # Check if initial voltage and power supply voltage match
    Vinitial_CHECK = float(ps.readVoltageAndCurrent()[0])
    if Vinitial != (int)(Vinitial_CHECK):
            raiseError('--Vinitial does not match starting power supply voltage: {0} V =/= {1} V'.format(str(Vinitial), str(Vinitial_CHECK)))
    print('--Vinitial correctly matches starting power supply voltage...')

    data = open(save_path, 'a')
    data.write('#Date-Time Voltage(V) Capacitance(F) Current(A) Resistance(Ohm) Frequency (kHz)\n')
    print('{0} created successfully...'.format(save_path))

    print('Opening plot window...')
    plot = CVPlotWindow()
    plot.open()

    if full_step:
        dV = Vstep_initiate
    else:
        dV = 0.1 if Vstep_initiate > 0 else -0.1

    N_small_steps = int(abs(Vstep_initiate / dV))
    N_big_steps = int(abs((Vstart - Vinitial) / Vstep_initiate))
    Vcurrent = Vinitial

    #Biasing up to first data point
    try:
        for i in range(N_big_steps):
            print('Ramping power supply to starting voltage.')
            #ps.triggerRead()
            voltage,current = ps.readVoltageAndCurrent()
            ps.controlAverage('off')

            print('Ramp to Vinitial: Ramping from {0} V to {1} V...'.format(str(Vcurrent), str(Vcurrent + Vstep_initiate)))

            for j in range(N_small_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)

            time.sleep(rest_time)

            if ps.inCompliance():
                COMPLIANCE_CHECK += 1

                while True:
                    time.sleep(WAIT_TIME_FOR_CHECK)
                    if ps.inCompliance():
                        COMPLIANCE_CHECK += 1
                    else:
                        COMPLIANCE_CHECK = 0
                        break
                    if COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                        raise HitCompliance

            ps.controlAverage('on')


    except HitCompliance:
        if kill_on_hit_comp:
            ps.shutdown()
            data.close()
            sys.exit(1)
        else:
            if Vcurrent > 0:
                dV = -0.1
            else:
                dV = 0.1
            N_rampDown_steps = int(abs(Vcurrent) / abs(dV))
            time.sleep(5)
            ps.controlAverage('off')
            for i in range(N_rampDown_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)
            data.close()

        print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
        return

    if full_step:
        dV = Vstep_run
    else:
        if Vstep_run > 0:
            dV = 0.1
        else:
            dV = -0.1

    N_small_steps = int(abs(Vstep_run/dV))
    N_big_steps = int(abs((Vfinal - Vstart) / Vstep_run))
    #if N_big_steps == 0:
    #    N_big_steps = 1
    Vcurrent = Vstart
    print("N_small_step= ",N_small_steps,"N_big_steps",N_big_steps,"Vcurren/vstartt=",Vcurrent)
    print('Waiting {0} s before first measurement'.format(str(first_point_rest_time)))
    time.sleep(first_point_rest_time)
    #print("V and I before main loop are",ps.readVoltageAndCurrent())

    try:

        print('Making a measurement...')
        #ps.triggerRead()
        voltage, current = ps.readVoltageAndCurrent()
        capacitance = lcr.readCapacitance()
        resistance = lcr.readResistance()

        date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
        capacitance_corrected = float(capacitance)     ###########- float(capacitance_open)
        measurement = [date_time, voltage, str(capacitance_corrected), current, resistance]
        data.write(' '.join(measurement) + '\n')

        plot.update(measurement)
        print('At {0}: V = {1} V, C = {2} F, I = {3} A, R = {4} Ohms.'.format(*measurement))

        # Loop though our big voltage steps
        for i in range(N_big_steps):
            ps.controlAverage('off')
            lcr.controlAverage('off')

            #print("V and I before mini ramp are",ps.readVoltageAndCurrent())

            #print('Ramping from {0} V to {1} V...'.format(str(Vcurrent), str(Vcurrent + Vstep_run)))
            for j in range(N_small_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)
            #print("V and I after mini ramp are",ps.readVoltageAndCurrent())

            #print('Waiting {0} s...'.format(str(rest_time)))
            time.sleep(rest_time)
            #print("V and I after sleep are",ps.readVoltageAndCurrent())

            # Check compliance
            if ps.inCompliance():
                COMPLIANCE_CHECK += 1
                WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))

                while True:

                    print('Waiting {0} s before checking compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                    time.sleep(WAIT_TIME_FOR_CHECK)
                    if ps.inCompliance():
                        COMPLIANCE_CHECK += 1
                        WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))
                    else:
                        print('Compliance check passed -- resetting check count.')
                        COMPLIANCE_CHECK = 0
                        break

                    if COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                        raise HitCompliance
            else:
                print ("Didn't hit compliance")
                
            # Turn back on the averaging prior to making a measurement
            #print("V and I before ps average are",ps.readVoltageAndCurrent())
            ps.controlAverage('on')
            #print("V and I before lcr average are",ps.readVoltageAndCurrent())
            lcr.controlAverage('on')
            #print("V and I before frequency loop are",ps.readVoltageAndCurrent())

            print('Making a measurement...')
            for frequency in lcrFrequencies:
                lcr.setFrequency(frequency)
                time.sleep(0.2) #wait to make sure frequency has been updated?
                #ps.triggerRead()
                voltage, current = ps.readVoltageAndCurrent()
                #print("test Voltage= ",voltage,"current=",current)
                capacitance = lcr.readCapacitance()
                resistance = lcr.readResistance()
                date_time = time.strftime('%Y/%m/%d-%H:%M:%S')

                capacitance_corrected = float(capacitance)    ##############- float(capacitance_open)
                measurement = [date_time, voltage, str(capacitance_corrected), current, resistance, (str)(frequency/1000.0)]
                data.write(' '.join(measurement) + '\n')
                plot.update(measurement)
                print('At {0}: V = {1} V, C = {2} F, I = {3} A, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

    # Catch our compliance exception
    except HitCompliance:

        ERROR('Failed compliance check {0} consecutive time(s)'.format(str(COMPLIANCE_CHECK_MAX)))

        print('Saving CV plot...')
        plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()

        # Perform concluding tasks and exit the program if --killOnHitComp = True
        if kill_on_hit_comp:

            print('Concluding run...')
            print('Closing power supply serial port...')
            ps.shutdown()
            print('Closing connection to LCR...')
            lcr.shutdown()
            print('Run finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            STATUS('Finished with error.', False)
            sys.exit(1)

        else:

            if Vcurrent > 0:
                dV = -0.5
            elif Vcurrent < 0:
                dV = 0.5

            N_rampDown_steps = int(abs(Vcurrent) / abs(dV))

            print('Waiting 5 s prior to ramping down...')
            time.sleep(5)
            print('Ramping down from {0} V to 0 V...'.format(str(Vcurrent)))

            ps.controlAverage('off')
            for i in range(0, N_rampDown_steps):
                Vcurrent += dV
                ps.setVoltage(Vcurrent)
                time.sleep(0.02)

            print('Ramp down finished.')
            print('Measurement finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
        print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
        return

    except Exception as e:

        print('***ERROR*** something has gone wrong - error message to follow...')

        print('Saving CV plot...')
        plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        print('Closing power supply serial port...')
        ps.shutdown()
        print('Closing connection to LCR...')
        lcr.shutdown()
        STATUS('Finished with error.', False)
        print('Python error message below:')
        raise(e)

    print('Measurement finished.')

    print('Saving CV plot...')
    plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    plot.close()
    print('Closing {0}...'.format(save_path))
    data.close()

    if ramp_down and Vfinal != 0:

        if Vfinal > 0:
            dV = -0.5
        else:
            dV = 0.5

        N_rampDown_steps = int(abs(Vfinal) / abs(dV))
        print('Waiting 5 s prior to ramping down...')
        time.sleep(5)
        print('Ramping from {0} V to 0 V...'.format(str(Vcurrent)))

        ps.controlAverage('off')
        for i in range(0, N_rampDown_steps):
            Vcurrent += dV
            ps.setVoltage(Vcurrent)
            time.sleep(0.02)

        print('Ramp down finished.')

    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))


def measureCV_SMU(ps,am,lcr,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time,lcrFrequencies):
    ''' IV test using two power supplies: ps is ramped to a fixed voltage for the test and ramped down after again, am performs IV sweep and ramps down after. '''

    # ps_Vinitial should be 0
    # am_Vinitial is measurement starting V --> need to set am_Vcurrent = 0
    am_Vcurrent = 0.

    #########################################################################################
    # Define the number of times we have to fail our compliance check to raise HitCompliance
    COMPLIANCE_CHECK_MAX = 5
    COMPLIANCE_CHECK = 0
    SMU_COMPLIANCE_CHECK = 0
    VSTEP_PER_CHECK = 0.5 # should probably be a multiple of 0.1
    WAIT_TIME_FOR_CHECK = 1.0
    #########################################################################################

    sht21 = False
    sht = 0

    # Check if initial voltage and power supply voltage match
    Vinitial_CHECK = float(ps.readVoltageAndCurrent()[0])
    if abs(ps_Vinitial- Vinitial_CHECK)>0.01:
            raiseError('--ps_Vinitial does not match starting power supply voltage: {0} V =/= {1} V'.format(str(ps_Vinitial), str(Vinitial_CHECK)))
    print('--ps_Vinitial correctly matches starting power supply voltage...')

    data = open(save_path, 'a')
    data.write('#Date-Time Voltage(V) Capacitance(F) Current(A) Resistance(Ohm) Frequency (kHz) \n')
    print('{0} created successfully...'.format(save_path))

    print('Opening plot window...')
    plot = CVPlotWindow()
    plot.open()
    print('Opening time plot window...')
    #timeplot = TimePlot()
    print('Finished with setup.')

    # Take dV to equal Vstep is full_step is specified
    if full_step:
        ps_dV = ps_Vstep
    else:
        if ps_Vstep > 0:
            ps_dV = 0.1
        else:
            ps_dV = -0.1

    # Get how many dV steps are in our voltage step size
    ps_N_small_steps = int(abs(ps_Vstep/ps_dV))
    # Get how many steps sizes are in our initial to final voltage range
    ps_N_big_steps = int(abs((ps_Vfinal - ps_Vinitial)/ps_Vstep))
    ps_Vcurrent = ps_Vinitial

    # Get the j values (index in our range(N_small_steps) loop below) where we want to perform compliance checking
    j_CHECK = int(abs(VSTEP_PER_CHECK / ps_dV))
    if j_CHECK < 1:
        j_CHECK = 1

    # Compliance checking function
    def checkCompliance():

        nonlocal COMPLIANCE_CHECK

        if ps.inCompliance():
            COMPLIANCE_CHECK += 1
            WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))

            while True:
                print('Waiting {0} s before checking compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                time.sleep(WAIT_TIME_FOR_CHECK)

                if ps.inCompliance():
                    COMPLIANCE_CHECK += 1
                    WARNING('Compliance check failed {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK)))
                else:
                    print('Compliance check passed -- resetting check count.')
                    COMPLIANCE_CHECK = 0
                    break

                if COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                    raise HitCompliance


    #Ramping HV PS
    try:

        for i in range(ps_N_big_steps + 1):

            print('Waiting {0} s...'.format(str(rest_time)))
            time.sleep(rest_time)

            voltage, current = ps.readVoltageAndCurrent()
            if i == ps_N_big_steps:
                break

            ps.controlAverage('off')

            voltage_low_check,current_low_check = am.readVoltageAndCurrent()

            print('Ramping from {0} V to {1} V...'.format(str(ps_Vcurrent), str(ps_Vcurrent + ps_Vstep)))
            for j in range(ps_N_small_steps):
                ps_Vcurrent += ps_dV
                ps.setVoltage(ps_Vcurrent)
                time.sleep(0.2)

                if ((j+1) % j_CHECK == 0):
                    checkCompliance()

            ps.controlAverage('on')

    except HitCompliance:

        ERROR('Failed compliance check {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK_MAX)))
        print('Saving CV plots...')
        plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
        print('Closing {0}...'.format(save_path))
        data.close()
        plot.close()

        if kill_on_hit_compliance:
            print('Closing power supply serial port...')
            ps.shutdown()
            print('Closing {0}...'.format(save_path))
            print('Run finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            STATUS('Finished with error.', False)
            sys.exit(1)

        else:

            if ps_Vcurrent > 0:
                ps_dV = -0.5
            else:
                ps_dV = 0.5

            ps_N_rampDown_steps = int(abs(ps_Vcurrent) / abs(ps_dV))

            print('Waiting 5 s prior to ramping down...')
            time.sleep(5)
            print('Ramping from {0} V to 0 V...'.format(str(ps_Vcurrent)))

            am.controlAverage('off')
            ps.controlAverage('off')

            for i in range(ps_N_rampDown_steps):
                ps_Vcurrent += ps_dV
                ps.setVoltage(ps_Vcurrent)
                time.sleep(0.02)

            print('PS ramp down finished.')
            print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))

        return

    # Compliance checking function for picoammeter
    def smu_checkCompliance():

        nonlocal SMU_COMPLIANCE_CHECK

        # If in compliance, increment our compliance check and stop ramping
        if am.inCompliance():
            SMU_COMPLIANCE_CHECK += 1
            WARNING('Picoammeter compliance check failed {0} consecutive time(s).'.format(str(SMU_COMPLIANCE_CHECK)))

            while True:
                print('Waiting {0} s before checking picoammeter compliance again...'.format(str(WAIT_TIME_FOR_CHECK)))
                time.sleep(WAIT_TIME_FOR_CHECK)

                if am.inCompliance():
                    SMU_COMPLIANCE_CHECK += 1
                    WARNING('SMU compliance check failed {0} consecutive time(s).'.format(str(SMU_COMPLIANCE_CHECK)))
                else:
                    print('Picoammeter compliance check passed -- resetting check count.')
                    SMU_COMPLIANCE_CHECK = 0
                    break

                # If we reach our max compliance check, throw an exception
                if SMU_COMPLIANCE_CHECK == COMPLIANCE_CHECK_MAX:
                    raise HitCompliance

    j_CHECK_SMU = 1

    ## SMU RAMPING
    if(am_Vinitial != 0):

        if am_Vinitial > am_Vcurrent:
            am_dV = 0.1
        else:
            am_dV = -0.1
        am_N_ramp_up_steps = int(abs(am_Vinitial - am_Vcurrent)/abs(am_dV))

        j_CHECK_SMU = int(abs(VSTEP_PER_CHECK / am_dV))
        if j_CHECK_SMU < 1:
            j_CHECK_SMU = 1

        am.controlAverage('off')
        print('Ramping picoammeter from {0} V to {1} V...'.format(str(am_Vcurrent), str(am_Vinitial)))

        try:

            for j in range(am_N_ramp_up_steps):
                am_Vcurrent += am_dV
                am.setVoltage(am_Vcurrent)
                time.sleep(0.5)
                if ((j+1) % j_CHECK_SMU == 0):
                    smu_checkCompliance()
            am.controlAverage('on')

        except HitCompliance:

            ERROR('Picoammeter failed compliance check {0} consecutive time(s).'.format(str(COMPLIANCE_CHECK_MAX)))
            print('Closing {0}...'.format(save_path))
            data.close()
            plot.close()

            if kill_on_hit_compliance:
                print('Closing power supply serial port...')
                ps.shutdown()
                am.shutdown()
                print('Closing {0}...'.format(save_path))
                print('Run finished at: {0}'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
                STATUS('Finished with error.', False)
                sys.exit(1)

            else:

                if ps_Vcurrent > 0:
                    ps_dV = -0.5
                else:
                    ps_dV = 0.5

                ps_N_rampDown_steps = int(abs(ps_Vcurrent) / abs(ps_dV))

                print('Waiting 5 s prior to ramping down...')
                time.sleep(5)
                print('Ramping PS from {0} V to 0 V...'.format(str(ps_Vcurrent)))

                am.controlAverage('off')
                ps.controlAverage('off')

                for i in range(ps_N_rampDown_steps):
                    ps_Vcurrent += ps_dV
                    ps.setVoltage(ps_Vcurrent)
                    time.sleep(0.02)
                print('PS ramp down finished.')

                if am_Vcurrent > 0:
                    am_dV = -0.5
                else:
                    am_dV = 0.5
                am_N_rampDown_steps = int(abs(am_Vcurrent) / abs(am_dV))

                print('Ramping picoammeter from {0} V to 0 V...'.format(str(am_Vcurrent)))

                for i in range(am_N_rampDown_steps):
                    am_Vcurrent += am_dV
                    am.setVoltage(am_Vcurrent)
                    time.sleep(0.2)

                print('Picoammeter ramp down finished.')

            print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
            return

    ### end SMU ramp up ###

    ps.controlAverage('on')
    am.controlAverage('on')

    ###
    # BEGIN MEASUREMENT
    ###

    if am_Vstep > 0:
        am_dV = 0.1
    else:
        am_dV = -0.1
    am_N_small_steps = int(abs(am_Vstep/am_dV))
    am_N_big_steps = int(abs((am_Vfinal - am_Vinitial)/am_Vstep))

    print('Waiting {} s before making first measurement.'.format(first_point_rest_time))
    time.sleep(first_point_rest_time)
    try:
        for i in range(am_N_big_steps + 1):
            print('Making a measurement...')
            myNAverages=5
            for x in range(myNAverages):
                for frequency in lcrFrequencies:
                    lcr.setFrequency(frequency)
                    time.sleep(0.5) #wait to make sure frequency has been updated?
                    am.triggerRead()
                    voltage, current = am.readVoltageAndCurrentFromBuffer()

                    capacitance = lcr.readCapacitance()
                    resistance = lcr.readResistance() 
                    #capacitance='10'
                    #resistance='10'
                    date_time = time.strftime('%Y/%m/%d-%H:%M:%S')

                    capacitance_corrected = float(capacitance)    ##############- float(capacitance_open)
                    measurement = [date_time, voltage, str(capacitance_corrected), current, resistance, (str)(frequency/1000.0)]
                    data.write(' '.join(measurement) + '\n')
                    plot.update(measurement)
                    print('At {0}: V = {1} V, C = {2} F, I = {3} A, R = {4} Ohms, F = {5} kHz.'.format(*measurement))


            if i == am_N_big_steps:
                break

            am.controlAverage('off')

            #ramp low voltage slowly
            for j in range(am_N_small_steps):
                am_Vcurrent += am_dV
                print('Ramping SMU to '+"{:.2f}".format(am_Vcurrent))
                am.setVoltage(am_Vcurrent)
                time.sleep(0.2)

                if ((j+1) % j_CHECK_SMU == 0):
                    smu_checkCompliance()

            am.controlAverage('on')

    except HitCompliance:

        if kill_on_hit_compliance:
            ps.shutdown()
            data.close()
            sys.exit(1)

        else:

            if am_Vcurrent > 0:
                am_dV = -0.5
            elif am_Vcurrent < 0:
                am_dV = 0.5

            am_N_rampDown_steps = int(abs(am_Vfinal)/abs(am_dV))
            time.sleep(5)
            am.controlAverage('off')

            for i in range(0, am_N_rampDown_steps):
                am_Vcurrent += am_dV
                am.setVoltage(am_Vcurrent)
                time.sleep(0.02)

            am.controlAverage('on')
            print('SMU ramp down finished.')

            if ps_Vcurrent > 0:
                ps_dV = -0.5
            elif ps_Vcurrent < 0:
                ps_dV = 0.5

            ps_N_rampDown_steps = int(abs(ps_Vcurrent)/abs(ps_dV))
            time.sleep(5)

            ps.controlAverage('off')
            for i in range(ps_N_rampDown_steps):
                ps_Vcurrent += ps_dV
                ps.setVoltage(ps_Vcurrent)
                time.sleep(0.02)
            ps.controlAverage('on')
            data.close()

        print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
        return

    print('Measurement finished.')

    print('Saving CV plots...')
    plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()

    if ramp_down and am_Vfinal != 0:

        if am_Vcurrent > 0:
            am_dV = -0.5
        elif am_Vcurrent < 0:
            am_dV = 0.5

        am_N_rampDown_steps = int(abs(am_Vfinal)/abs(am_dV))

        time.sleep(5)

        am.controlAverage('off')
        for i in range(0, am_N_rampDown_steps):
            am_Vcurrent += am_dV
            am.setVoltage(am_Vcurrent)
            time.sleep(0.02)

        print('SMU ramp down finished.')

    if ramp_down and ps_Vfinal != 0:

        if ps_Vcurrent > 0:
            ps_dV = -0.5
        elif ps_Vcurrent < 0:
            ps_dV = 0.5
        ps_N_rampDown_steps = int(abs(ps_Vfinal) / abs(ps_dV))

        print('Waiting 5 s prior to ramping down...')
        time.sleep(5)
        print('Ramping from {0} V to 0 V...'.format(str(ps_Vcurrent)))

        ps.controlAverage('off')
        for i in range(0, ps_N_rampDown_steps):
            ps_Vcurrent += ps_dV
            ps.setVoltage(ps_Vcurrent)
            time.sleep(0.02)

        print('PS ramp down finished.')

    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))



if __name__ == '__main__':
    pass
