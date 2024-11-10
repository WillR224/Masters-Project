#!/usr/bin/python
# runIVCV.py -- main script for running IV and CV tests
# Updated: 05/03/2021
# Contributing: Will George (University of Birmingham)

from __future__ import print_function
import sys, os, time, platform, csv
import os.path
#from Devices import Keithley2410
#from Devices import Keithley2470
#from Devices import Keithley6487
#from Devices import KeysightE4980AL
from Devices import Keithley6517
#from Devices import WayneKerr6500B
from MeasurementFunctions import measureCV
from MeasurementFunctions import measureIV_PS
from MeasurementFunctions import measureIV_SMU
from MeasurementFunctions import measureCV_SMU
import TestFunctions as tests
from MeasurementFunctions import ERROR
from datetime import datetime
import colorama
import pyvisa as visa

def main(test):

    colorama.init(autoreset=True) #used for colour printing    
    
    #look for devices
    '''
    rm= visa.ResourceManager()
    devices=[x for x in rm.list_resources()]
    for device in devices:
        print (device)
        #print(rm.open_resource((str)(device)).query("*IDN?"))
        try:
            print(rm.open_resource((str)(device)).query("*IDN?\n"))
        except:
            print("Couldn't ID")    

    exit()
    '''
    
    #Set up HV SMU
    
    print('Setting up HV SMU.')
    psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
    psCompliance = 10.0E-6  #compliance of power supply in A
    psAverage = 1         #power supply internal measurement averaging
    #ps = Keithley2410(str(psPort),psCompliance,psAverage)
    ps = Keithley6517(str(psPort),psCompliance,psAverage)
    
    #psID = 'GPIB0::21::INSTR' #GPIB interface number (name can be found using NI-MAX)
    #psCompliance = 10.0E-6     #compliance in A
    #psCurrentRange = 1e-6    #current range in A
    #psAverage = 5             #picoammeter internal measurement averaging
    #ps = Keithley2470(psID,psCompliance,psAverage)
    #ps = Keithley6517(psID,psCompliance,psAverage)
    try:
        ps.setup()
    except Exception as e:
        print (e)
        ERROR('HV SMU setup failed.')
        return 1
    current_range = psCompliance
    ps.setCurrentRange(current_range)
    ps.controlSource('on') #apply voltage
    print('HV SMU setup successful.')
  
    if (False):
        #Set up LCR meter
        print('Setting up LCR meter.')
        lcrID = 'GPIB1::15::INSTR' #GPIB interface number (name can be found using NI-MAX)
        lcrFreq = 10E3            #measurement frequency in Hz
        lcrLevel = 0.1            #AC output voltage in V
        lcrAverage = 3           #LCR internal measurement averaging
        lcr = WayneKerr6500B(lcrID,lcrFreq,lcrLevel,lcrAverage)
        
        try:
            lcr.setup()
        except:
            ERROR('LCR meter setup failed.')
            return 1
        print('LCR meter setup successful.')
        
        #LCR open correction
        #print("Performing lcr open correction.")
        #lcr.openCorrectionToggle('on')
        #lcr.shortCorrectionToggle('on')
        #lcr.openCorrection()
        #time.sleep(30.)
        
        
        #Set up LV SMU
        print('Setting up LV SMU.')
        amID = 'GPIB0::18::INSTR' #GPIB interface number (name can be found using NI-MAX)
        amCompliance = 1.0E-6     #compliance in A
        amCurrentRange = 1e-6    #current range in A
        amAverage = 1             #picoammeter internal measurement averaging
        am = Keithley2470(amID,amCompliance,amAverage)
        try:
            am.setup()
        except:
            ERROR('LV SMU setup failed.')
            return 1
        am.setCurrentRange(amCurrentRange)
        am.controlSource('on') #apply voltage

        print('LV SMU setup successful.')
    
	
    if test == 'test':
        ''' 
        am.inCompliance()
        for v in range(0,10,1):
            am.setVoltage(v)
            #voltage, current= am.readVoltageAndCurrent()
            am.triggerRead()
            voltage,current=am.readVoltageAndCurrentFromBuffer()
            print("V=", voltage, "current=", current)
            time.sleep(0.02)

        am.controlSource('off')
        
        ps.setVoltage(0.0)
        voltage, current= ps.readVoltageAndCurrent()
        print("V=", voltage, "current=", current)
        
        ps.setVoltage(0.0)
        ps.triggerRead()
        voltage, current = ps.readVoltageAndCurrentFromBuffer()
        print("V=", voltage, "current=", current)
        
        print("Hit compliance?",ps.inCompliance())
        
        ps.controlSource("off")
        
        ps.controlAverage("off")
        
        ps.controlAutoRange("on")
        
        print("NAverages= ",ps.getAverage())
        ps.setAverage(2)
        print("NAverages= ",ps.getAverage())
        
        ps.setCompliance(2.0E-6)
        ps.controlSource("off")
        '''
        #ps.shutdown()
        
        lcr.setFrequency(1000)
        print("Capacitance=",lcr.readCapacitance())
        sys.exit(0)
        
    elif test == 'testWK':
        print ("Running WK test")

        #print("Capacitance=",lcr.readCapacitance())
        #print("CapacitanceOnce=",lcr.readCapacitanceOnce())
        #print("Resistance=",lcr.readResistance())
        #print("ResistanceOnce=",lcr.readResistanceOnce())
        #lcr.triggerRead() 
        #print("Capacitancefrombuffer=",lcr.readCapacitanceFromBuffer())
        #print("Resistancefrombuffer=",lcr.readResistanceFromBuffer())
        lcr.setFrequency(1E3)
        lcr.setLevel(0.1)
        lcr.setEquivCirc(0)
        print("WK test complete")
        sys.exit(0)


   
    #Simple IV measurement using Keithley 2410 
    elif test == 'IV':
        print('Performing IV measurement with Keithley 2410.')
        
        ps_Vinitial = 0.   #Starting voltage, V - this must be 0 at the moment as pre-measurement ramping is not implemented in measureIV_PS
        ps_Vfinal = -10.  #End voltage, V
        ps_Vstep = -2.    #Voltage step size, V [ensure sign is correct]
        rest_time = 5.    #Waiting time before measurement after ramping, s
        first_point_rest_time = 5. #Additional waiting time before first voltage step, s

        psCompliance = 10E-6
        Imax = psCompliance #measurement stops if measured current > Imax
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'Micron_210720_test.txt' #name for output data file
        
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
    elif test == 'IV_SMU':
        print('Performing IV measurement with Keithley 2410 and Keithley 2470.')
        
        #Setting ps_Vfinal to 0 V allows for measurement with only Keithley 6487

        ps_Vinitial = 0   #starting HV voltage, should be 0, V
        ps_Vfinal = -10. #constant HV to be applied by ps during measurement, V
        ps_Vstep = -2    #ramping step for HV SMU, V [ensure sign is correct]
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

        outputFile = 'testIV_interStrip.txt' #name for output data file

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
    elif test == 'CV':
        print('Performing CV measurement using Keithley2410 and Keysight LCR.')

        ps_Vinitial = 0.         #starting HV voltage, should be 0, V
        ps_Vstart = 0.          #first measurement voltage, V
        ps_Vstep_initiate = -1.0  #Vstep used to ramp to starting voltage [ensure sign is correct]
        ps_Vfinal = -500.        #final measurement voltage, V
        ps_Vstep_run = -2.      #measurement voltage step, V [ensure sign is correct]
        rest_time = 5.          #waiting time before measurement after ramping, s
        first_point_rest_time = 15. #Additional waiting time before first voltage step, s

        psCompliance = 1E-6   #ps compliance in A
        lcrFreq = [10E3]         #LCR measurement frequency, Hz
        lcrLevel = 0.1         #LCR AC output voltage, V
        lcrCircuit = 'CSRS'    #LCR equivalent circuit model

        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'MD8CV_2470_python_oldConnectorBox.txt' #name for output data file

        lcr.setFrequency(lcrFreq[0])
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
        lcrFreq_kHz = lcrFreq[0]/1000.0
        file.write('Frequency: ' + str(lcrFreq_kHz) + 'kHz \n')
        file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
        file.write('Circuit: ' + lcrCircuit + '\n')
        file.close()

        #run the test
        measureCV(ps,lcr,outputFile,ps_Vinitial,ps_Vstart,ps_Vfinal,ps_Vstep_initiate,ps_Vstep_run,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time, lcrFreq)

    elif test == 'CV_SMU':
        print('Performing IV measurement with Keithley 2410 and Keithley 2470.')
        
        #AW 1MHz, 500mV seems to work well for micron!!!!
        
        #Setting ps_Vfinal to 0 V allows for measurement with only Keithley 6487

        ps_Vinitial = 0   #starting HV voltage, should be 0, V
        ps_Vfinal = -60. #constant HV to be applied by ps during measurement, V
        ps_Vstep = -2.    #ramping step for HV SMU, V [ensure sign is correct]
        am_Vinitial = -5  #first measurement voltage, V
        am_Vfinal = 5     #last measurement voltage, V
        am_Vstep = 0.5    #measurement voltage step, V [ensure sign is correct]
        rest_time = 1.0   #waiting time before measurement after ramping, s
        first_point_rest_time = 10. #Additional waiting time before first voltage step, s

        amCompliance = 100E-6    #am compliance in A
        amCurrentRange = 10E-6  #current range in A
        psCompliance = 90E-6   #ps compliance in A
        
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_comp = False #if true, measurement stops without ramping down if compliance is reached

        save_path = 'test_micron_interStripCV_series_bias60V_AC100mV.txt' #name for output data file

        am.controlAverage('off')
        am.setCompliance(amCompliance)
        am.setCurrentRange(amCurrentRange)
        am.controlAverage('on')
        ps.controlAverage('off')
        ps.setCompliance(psCompliance)
        ps.controlAverage('on')
        
        lcrFrequencies = [1E3,1E4,1E5,1E6,1E7]         #LCR measurement frequency, Hz, can supply list
        #lcrFrequencies = [1E6]         #LCR measurement frequency, Hz, can supply list
        lcrLevel = 0.100         #LCR AC output voltage, V
        lcrCircuit = 'CSRS'    #LCR equivalent circuit model
        #lcrCircuit = 'CPRP'    #LCR equivalent circuit model
        lcr.setFrequency(lcrFrequencies[0])
        lcr.setLevel(lcrLevel)
        lcr.setFunctionType(lcrCircuit)

        now = datetime.now()
        currentTime = now.strftime("%H:%M")
        file = open(save_path,'a')
        file.write('Test Type: CV_SMU\n')
        file.write(currentTime+'\n')
        file.write('Frequency: ' + str(lcrFrequencies[0]/1000.0) + 'kHz \n')
        file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
        file.write('Circuit: ' + lcrCircuit + '\n')
        file.close()
        
        #run the test
        measureCV_SMU(ps,am,lcr,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time, lcrFrequencies)

    elif test=="newIV":
        #do stuff
        print('Performing IV measurement with Keithley 2410.')
        
        ps_Vinitial = 0.   #Starting voltage, V 
        ps_Vfinal = -60.  #End voltage, V
        ps_Vstep = -2.    #Voltage step size, V [ensure sign is correct]
        rest_time = 5.    #Waiting time before measurement after ramping, s
        first_point_rest_time = 5. #Additional waiting time before first voltage step, s

        psCompliance = 100E-6
        Imax = psCompliance #measurement stops if measured current > Imax
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached
    
        outputFile = 'test.txt' #name for output data file
        
        ps.controlAverage('off')
        ps.setCompliance(psCompliance)
        ps.setCurrentRange(psCompliance)
        ps.controlAverage('on')

        now = datetime.now()
        currentTime = now.strftime("%H:%M")
        file = open(outputFile,'a')
        file.write('Test Type: IV\n')
        file.write(currentTime+'\n')
        file.close()

        #run the test
        successStatus=tests.measureIV(ps,outputFile,ps_Vstep,ps_Vinitial,ps_Vfinal,Imax,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)
        if successStatus==0:
            print("Successfull test")
        else: 
            print("Test failed, see above")

    #IV using two power supplies; 'ps' applies a fixed voltage while 'am' performs IV sweep
    elif test == 'newIV_SMU':
        print('Performing IV measurement with Keithley 2410 and Keithley 2470.')
        
        #Setting ps_Vfinal to 0 V allows for measurement with only Keithley 6487

        ps_Vinitial = 0   #starting HV voltage, should be 0, V
        ps_Vfinal = -6. #constant HV to be applied by ps during measurement, V
        ps_Vstep = -2    #ramping step for HV SMU, V [ensure sign is correct]
        am_Vinitial = -5  #first measurement voltage, V
        am_Vfinal = 5     #last measurement voltage, V
        am_Vstep = 1.0    #measurement voltage step, V [ensure sign is correct]
        rest_time = 2   #waiting time before measurement after ramping, s
        first_point_rest_time = 2. #Additional waiting time before first voltage step, s

        amCompliance = 1E-6    #am compliance in A
        amCurrentRange = 2e-6  #current range in A
        psCompliance = 50E-6   #ps compliance in A
        
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'testIV_interStrip.txt' #name for output data file

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
        successStatus=tests.measureInterstripIV(ps,am,outputFile,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)

        if successStatus==0:
            print("Successfull test")
        else: 
            print("Test failed, see above")


    #Simple CV measurement using Keithley2410 and Keysight LCR
    elif test == 'newCV':
        print('Performing CV measurement using Keithley2410 and Keysight LCR.')

        ps_Vinitial = 0.         #starting HV voltage, should be 0, V
        ps_Vstart = 0.          #first measurement voltage, V
        ps_Vstep_initiate = -1.0  #Vstep used to ramp to starting voltage [ensure sign is correct]
        ps_Vfinal = -6.        #final measurement voltage, V
        ps_Vstep_run = -2.      #measurement voltage step, V [ensure sign is correct]
        rest_time = 5.          #waiting time before measurement after ramping, s
        first_point_rest_time = 15. #Additional waiting time before first voltage step, s

        psCompliance = 1E-6   #ps compliance in A
        lcrFreq = [10E6]         #LCR measurement frequency, Hz
        lcrLevel = 0.1         #LCR AC output voltage, V
        lcrCircuit = 'CSRS'    #LCR equivalent circuit model

        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        outputFile = 'testCV.txt' #name for output data file

        lcr.setFrequency(lcrFreq[0])
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
        lcrFreq_kHz = lcrFreq[0]/1000.0
        file.write('Frequency: ' + str(lcrFreq_kHz) + 'kHz \n')
        file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
        file.write('Circuit: ' + lcrCircuit + '\n')
        file.close()

        #run the test
        successStatus=tests.measureCV(ps,lcr,outputFile,ps_Vinitial,ps_Vstart,ps_Vfinal,ps_Vstep_initiate,ps_Vstep_run,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time, lcrFreq)
        if successStatus==0:
            print("Successfull test")
        else: 
            print("Test failed, see above")

    elif test == 'newCV_SMU':
        print('Performing IV measurement with Keithley 2410 and Keithley 2470.')
        
        #AW 1MHz, 500mV seems to work well for micron!!!!
        
        #Setting ps_Vfinal to 0 V allows for measurement with only Keithley 6487

        ps_Vinitial = 0   #starting HV voltage, should be 0, V
        ps_Vfinal = -60. #constant HV to be applied by ps during measurement, V
        ps_Vstep = -2.    #ramping step for HV SMU, V [ensure sign is correct]
        am_Vinitial = 0.0  #first measurement voltage, V
        am_Vfinal = 5     #last measurement voltage, V
        am_Vstep = 0.5    #measurement voltage step, V [ensure sign is correct]
        rest_time = 5.0   #waiting time before measurement after ramping, s
        first_point_rest_time = 10. #Additional waiting time before first voltage step, s

        amCompliance = 10E-6    #am compliance in A
        amCurrentRange = 10E-6  #current range in A
        psCompliance = 10E-6   #ps compliance in A
        psCurrentRange = 10E-6   #ps current range in A
        
        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_comp = False #if true, measurement stops without ramping down if compliance is reached

        save_path = 'micronInterstripCapacitance_parallel_500mV_1MHz.txt' #name for output data file

        am.controlAverage('off')
        am.setCompliance(amCompliance)
        am.setCurrentRange(amCurrentRange)
        am.controlAverage('on')
        ps.controlAverage('off')
        ps.setCompliance(psCompliance)
        ps.setCurrentRange(psCurrentRange)
        ps.controlAverage('on')
        
        #lcrFrequencies = [1E3,1E4,1E5,1E6,1E7]         #LCR measurement frequency, Hz, can supply list
        lcrFrequencies = [1E6]         #LCR measurement frequency, Hz, can supply list
        lcrLevel = 0.500         #LCR AC output voltage, V
        #lcrCircuit = 'CSRS'    #LCR equivalent circuit model
        lcrCircuit = 'CPRP'    #LCR equivalent circuit model
        lcr.setFrequency(lcrFrequencies[0])
        lcr.setLevel(lcrLevel)
        lcr.setFunctionType(lcrCircuit)

        now = datetime.now()
        currentTime = now.strftime("%H:%M")
        file = open(save_path,'a')
        file.write('Test Type: CV_SMU\n')
        file.write(currentTime+'\n')
        file.write('Frequency: ' + str(lcrFrequencies[0]/1000.0) + 'kHz \n')
        file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
        file.write('Circuit: ' + lcrCircuit + '\n')
        file.close()
        
        #run the test
        #successStatus=tests.measureInterstripCV(ps,am,lcr,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time, lcrFrequencies)
        successStatus=tests.measureInterstripCV_Phil(ps,am,lcr,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time, lcrFrequencies)
        if successStatus==0:
            print("Successfull test")
        else: 
            print("Test failed, see above")


    elif test=="jmIV":
            #Jonathan Mulvey
            #My version of this code
            
            #The 6517 doesn't allow you to set compliance (It might, but the functions we have don't let you. Nevertheless, we don't need it.
            #We can check for a maximum current and have our own built in compliance
            #We then need to make 2 more changes
            #1) is just the format we write to. I'd like to write to my own personal format to make it easier to plot etc
            #2) Is to rewrite the current scale. At the moment it is set to the compliance (uA) which means we don't measure pA very well. 
            #Rather than setting to auto range, we can try and do this range manually. Lets test this first to understand what happens when you go out of range
                        
            #So when it goes out of limit, it jumps VERY high. So we can just check that a limit has been reached
            
            #Two extra things for us to add here:
            #Firstly some comments to put at the start.
            #Just like we do in the LabView program
            
            #Next I would like to add comments to each measurement step.
            #So if we have to change the current step, we say that!
            
            
            ##SOMETHING TO NOTE ABOUT THE ERRORCODE -213 YOU WILL SEE
            #According to the internet (as any good science should start)...
            #The Read? command contains an INIT command within it, yet the device is
            #already initialised. So it throws the error and moves on. It doesn't break anything,
            #so I didn't see the need to fix it yet...
            
            
            
            print('Performing IV measurement with Keithley 6517.')
            
            ps_Vinitial = 0.   #Starting voltage, V 
            ps_Vfinal = -20.  #End voltage, V
            ps_Vstep = -4.    #Voltage step size, V [ensure sign is correct]
            rest_time = 5.    #Waiting time before measurement after ramping, s
            first_point_rest_time = 5. #Additional waiting time before first voltage step, s

            psCompliance = 3e-4
            psInitialCurrentRange = -12
            psMaxCurrentRange = -3
            Imax = psCompliance #measurement stops if measured current > Imax
            full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
            ramp_down=True      #ramp PS down to 0 V after measurement
            kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached
        
            outputFile = 'Results/test.txt' #name for output data file
            pltFormatFile = "Results/Batch1_Wafer21_LGAD_Diced_C5.txt"
            
            ans = "Y"
            if os.path.isfile(pltFormatFile):
                print("A file with the path: " + str(pltFormatFile) + " already exists, are you sure you want to continue? (Y/N)")
                
                while True:
                    ans = input("Response:")
                    if ans == "N":
                        print("Program will end")
                        break
                    elif ans == "Y":
                        print("File will be overwritten")
                        break
                    else:
                        print("Make sure your response is either a \"Y\" or a \"N\"")
                        
            if ans == "Y":
            
                ps.controlAverage('off')
                ps.setCompliance(psCompliance)
                ps.setCurrentRange(pow(10, psInitialCurrentRange))
                ps.controlAverage('on')

                initComments = "\n";
                initComments = initComments + "Comments:" + "\n"
                initComments = initComments + "Pad only; Floating" + "\n"
                initComments = initComments + "@Start" + "\n"
                initComments = initComments + "T = +20 deg C; RH = 0.538 V" + "\n"
                initComments = initComments + "@End" + "\n"
                initComments = initComments + "T = +20 deg C; RH = 0. V" + "\n"
                initComments = initComments + "" + "\n"

                now = datetime.now()
                currentTime = now.strftime("%H:%M")
                file = open(outputFile,'a')
                file.write('Test Type: ' + test + '\n')
                file.write(currentTime+'\n')
                file.write(initComments)
                file.close()        
                
                file = open(pltFormatFile,'w')
                file.write('Test Type: ' + test + '\n')
                file.write(currentTime+'\n')
                file.write(initComments)
                file.close()

                #Rather than giving a step etc, we are going to give the Test Function an array of voltages  for it to test. This allows us to use different steps at different points            
                ps_Voltages = []
                
                #For Testing
                end = -50
                #for i in range(-0, end, -5):
                #    ps_Voltages.append(i)
                #ps_Voltages.append(end)
                
                end = -100
                for i in range(-0, end, -1):
                    ps_Voltages.append(i)
                ps_Voltages.append(end)
                
                end = -900
                for i in range(-100, end, -2):
                    ps_Voltages.append(i)
                ps_Voltages.append(end)
                    
                #A common problem in the old LabView was that you would end up testing the same voltage twice when a different step was used
                #We will do a very quick and simple check here to make sure that doesn't happen
                old_ps_Voltages = ps_Voltages
                ps_Voltages = []
                print ("Checking Voltages for overlap")
                for i in range(len(old_ps_Voltages)):           
                    if i > 0:
                        #print(old_ps_Voltages[i], old_ps_Voltages[i-1])
                        if old_ps_Voltages[i] == old_ps_Voltages[i-1]:
                            print("Voltage overlap @ " + str(old_ps_Voltages[i]) + "V removed")
                            continue #Skip to the next one and don't add it
                    ps_Voltages.append(old_ps_Voltages[i])
                    
                #print (ps_Voltages)
                #The idea behind this chance is to hopefully allow me to stopa program mid test and just quit immediately
                    
                #run the test
                #successStatus=tests.jmMeasureIV(ps,outputFile,ps_Voltages,Imax,psInitialCurrentRange,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)
                successStatus = 1;
                try:
                    successStatus=tests.jmMeasureIV(ps,outputFile,pltFormatFile,ps_Voltages,Imax,psInitialCurrentRange,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)
                except KeyboardInterrupt:
                    print('Interrupted')
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                
                
                if successStatus==0:
                    print("Successfull test")
                else: 
                    print("Test failed, see above")





    #Close connections to instruments
    print('Test finished - shutting down instruments.')
    
    print("")
    print("")
    print("")
    
    ps.controlSource('off')
    ps.shutdown()
    #lcr.shutdown()
    #am.controlSource('off')
    #am.shutdown()

    colorama.deinit()



    return 0


if __name__ == "__main__":

    argv = sys.argv[1:]
    if not argv:
        print('Please enter \'IV\', \'IV_SMU\' or \'CV\' as first argument:')
        print('    IV - simple IV calling measureIV_PS function.')
        print('    IV_SMU - IV with two power supplies calling measureIV_SMU function.')
        print('    CV - simple CV calling measureCV function.')
        print('    CV_SMU - CV with two power supplies calling measureCV_SMU function.')
        sys.exit(0)

    try:
        main(argv[0])
    except KeyboardInterrupt:
        sys.exit(1)
