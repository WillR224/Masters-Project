#!/usr/bin/python
# runIVCV.py -- main script for running IV and CV tests
# Updated: 05/03/2021
# Contributing: Will George (University of Birmingham)

from __future__ import print_function
import sys, os, time, platform, csv
from Devices import Keithley2410
from Devices import Keithley2470
from Devices import Keithley6487
from Devices import KeysightE4980AL
from Devices import Keithley6517
from Devices import WayneKerr6500B
from MeasurementFunctions import measureCV
from MeasurementFunctions import measureIV_PS
from MeasurementFunctions import measureIV_SMU
from MeasurementFunctions import ERROR
from datetime import datetime
import colorama

def main(test):

    colorama.init(autoreset=True) #used for colour printing    

    #Set up HV SMU
    print('Setting up HV SMU.')
    psPort = 'GPIB::21::INSTR'        #serial port to connect (port name can be found using NI-MAX)
    psCompliance = 1.0E-6  #compliance of power supply in A
    psAverage = 1          #power supply internal measurement averaging
    ps = Keithley2470(psPort,psCompliance,psAverage)
    try:
        ps.setup()
    except:
        ERROR('HV SMU setup failed.')
        return 1
    current_range = psCompliance
    ps.setCurrentRange(current_range)
    ps.controlSource('on') #apply voltage
    print('HV SMU setup successful.')

    #Set up LCR meter
    print('Setting up LCR meter.')
    lcrID = 'GPIB::18::INSTR' #GPIB interface number (name can be found using NI-MAX)
    lcrFreq = 10E3            #measurement frequency in Hz
    lcrLevel = 1.0            #AC output voltage in V
    lcrAverage = 16           #LCR internal measurement averaging
    lcr = KeysightE4980AL(lcrID,lcrFreq,lcrLevel,lcrAverage)
    try:
        lcr.setup()
    except:
        ERROR('LCR meter setup failed.')
        return 1
    print('LCR meter setup successful.')

    #Set up LV SMU
    print('Setting up LV SMU.')
    amID = 'GPIB0::29::INSTR' #GPIB interface number (name can be found using NI-MAX)
    amCompliance = 2.5E-3     #compliance in A
    amCurrentRange = 10e-6    #current range in A
    amAverage = 1             #picoammeter internal measurement averaging
    am = Keithley6487(amID,amCompliance,amAverage)
    try:
        am.setup()
    except:
        ERROR('LV SMU setup failed.')
        return 1
    am.setCurrentRange(amCurrentRange)
    print('LV SMU setup successful.')

    #LCR open correction
    #print("Performing lcr open correction.")
    #lcr.openCorrectionToggle('on')
    #lcr.shortCorrectionToggle('on')
    #lcr.openCorrection()
    #time.sleep(30.)
   
    #Simple IV measurement using Keithley 2410 
    if test == 'IV':
        print('Performing IV measurement with Keithley 2410.')
        
        ps_Vinitial = 0.   #Starting voltage, V - this must be 0 at the moment as pre-measurement ramping is not implemented in measureIV_PS
        ps_Vfinal = -700.  #End voltage, V
        ps_Vstep = -10.    #Voltage step size, V [ensure sign is correct]
        rest_time = 10.    #Waiting time before measurement after ramping, s
        first_point_rest_time = 1. #Additional waiting time before first voltage step, s

        psCompliance = 50E-6
        Imax = psCompliance #measurement stops if measured current > Imax
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'test.txt' #name for output data file
        
        ps.controlAverage('off')
        ps.setCompliance(psCompliance)
        ps.controlAverage('on')

        now = datetime.now()
        currentTime = now.strftime("%H:%M")
        file = open(outputFile,'a')
        file.write('Test Type: IV\n')
        file.write(currentTime+'\n')
        file.close()

        #run the test
        measureIV_PS(ps,outputFile,ps_Vstep,ps_Vinitial,ps_Vfinal,Imax,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)
    
    
    #IV using two power supplies; 'ps' applies a fixed voltage while 'am' performs IV sweep
    if test == 'IV_SMU':
        print('Performing IV measurement with Keithley 2410 and Keithley 6487.')
        
        #Setting ps_Vfinal to 0 V allows for measurement with only Keithley 6487

        ps_Vinitial = 0   #starting HV voltage, should be 0, V
        ps_Vfinal = -500. #constant HV to be applied by ps during measurement, V
        ps_Vstep = -10    #ramping step for HV SMU, V [ensure sign is correct]
        am_Vinitial = -5  #first measurement voltage, V
        am_Vfinal = 5     #last measurement voltage, V
        am_Vstep = 1.0    #measurement voltage step, V [ensure sign is correct]
        rest_time = 0.2   #waiting time before measurement after ramping, s
        first_point_rest_time = 10. #Additional waiting time before first voltage step, s

        amCompliance = 1E-6    #am compliance in A
        amCurrentRange = 2e-6  #current range in A
        psCompliance = 50E-6   #ps compliance in A
        
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'test.txt' #name for output data file

        am.controlAverage('off')
        am.setCompliance(amCompliance)
        am.setCurrentRange(amCurrentRange)
        am.controlAverage('on')
        ps.controlAverage('off')
        ps.setCompliance(psCompliance)
        ps.controlAverage('on')

        now = datetime.now()
        currentTime = now.strftime("%H:%M")
        file = open(outputFile,'a')
        file.write('Test Type: IV\n')
        file.write(currentTime+'\n')
        file.close()
        
        #run the test
        measureIV_SMU(ps,am,outputFile,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)


    #Simple CV measurement using Keithley2410 and Keysight LCR
    if test == 'CV':
        print('Performing CV measurement using Keithley2410 and Keysight LCR.')

        ps_Vinitial = 0.         #starting HV voltage, should be 0, V
        ps_Vstart = 10.          #first measurement voltage, V
        ps_Vstep_initiate = 5.0  #Vstep used to ramp to starting voltage [ensure sign is correct]
        ps_Vfinal = -700.        #final measurement voltage, V
        ps_Vstep_run = -10.      #measurement voltage step, V [ensure sign is correct]
        rest_time = 15.          #waiting time before measurement after ramping, s
        first_point_rest_time = 15. #Additional waiting time before first voltage step, s

        psCompliance = 50E-6   #ps compliance in A
        lcrFreq = 10E3         #LCR measurement frequency, Hz
        lcrLevel = 0.1         #LCR AC output voltage, V
        lcrCircuit = 'CSRS'    #LCR equivalent circuit model

        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'test.txt' #name for output data file

        lcr.setFrequency(lcrFreq)
        lcr.setLevel(lcrLevel)
        lcr.setFunctionType(lcrCircuit)
        ps.controlAverage('off')
        ps.setCompliance(psCompliance)
        ps.controlAverage('on')

        now = datetime.now()
        currentTime = now.strftime("%H:%M")
        file = open(outputFile,'a')
        file.write('Test Type: CV\n')
        file.write(currentTime+'\n')
        lcrFreq_kHz = lcrFreq/1000
        file.write('Frequency: ' + str(lcrFreq_kHz) + 'kHz \n')
        file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
        file.write('Circuit: ' + lcrCircuit + '\n')
        file.close()

        #run the test
        measureCV(ps,lcr,outputFile,ps_Vinitial,ps_Vstart,ps_Vfinal,ps_Vstep_initiate,ps_Vstep_run,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)


    #Close connections to instruments
    print('Test finished - shutting down instruments.')
    ps.controlSource('off')
    ps.shutdown()
    lcr.shutdown()
    am.controlSource('off')
    am.shutdown()

    colorama.deinit()

    return 0


if __name__ == "__main__":

    argv = sys.argv[1:]
    if not argv:
        print('Please enter \'IV\', \'IV_SMU\' or \'CV\' as first argument:')
        print('    IV - simple IV calling measureIV_PS function.')
        print('    IV_SMU - IV with two power supplies calling measureIV_SMU function.')
        print('    CV - simple CV calling measureCV function.')
        sys.exit(0)
    if(argv[0] != 'IV' and argv[0] != 'IV_SMU' and argv[0] != 'CV'):
        print('Please enter \'IV\', \'IV_SMU\' or \'CV\' as first argument:')
        print('    IV - simple IV calling measureIV_PS function.')
        print('    IV_SMU - IV with two power supplies calling measureIV_SMU function.')
        print('    CV - simple CV calling measureCV function.')
        sys.exit(0)

    try:
        main(argv[0])
    except KeyboardInterrupt:
        sys.exit(1)
