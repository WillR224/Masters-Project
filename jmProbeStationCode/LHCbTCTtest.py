#!/usr/bin/python
# runIVCV.py -- main script for running IV and CV tests
# Updated: 05/03/2021
# Contributing: Will George (University of Birmingham)

from __future__ import print_function
import sys, os, time, platform, csv
import os.path
from Devices import Keithley2410
#from Devices import Keithley2470
from Devices import Keithley6487
from Devices import KeysightE4980AL
from Devices import Keithley6517
from Devices import Keithley6517_Serial
from Devices import AgilentMSO9254A
from Devices import MX180TP
from Devices import XilabController
#from Devices import WayneKerr6500B
from MeasurementFunctions import measureCV
from MeasurementFunctions import measureIV_PS
from MeasurementFunctions import measureIV_SMU
from MeasurementFunctions import measureCV_SMU
import LHCbTCTTestFunctions as tests #changed this to my test functions file
from MeasurementFunctions import ERROR
from datetime import datetime
import colorama
import pyvisa as visa
import serial
from distutils.dir_util import copy_tree
import itertools
import numpy as np

def main(test):

    print("Test = " + test)

    colorama.init(autoreset=True) #used for colour printing    
    
    ps = None #Just to make sure it is defined
    
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

    #Simple CV measurement using Keithley2410 and Keysight LCR
    elif test == 'jmCV':
        #Set up HV SMU
        print('Setting up HV SMU.')
        #psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        #psCompliance = 10.0E-6  #compliance of power supply in A
        #psAverage = 1         #power supply internal measurement averaging
        #ps = Keithley2410(str(psPort),psCompliance,psAverage)
        #ps = Keithley6517(str(psPort),psCompliance,psAverage)
            
        psID = 'GPIB0::29::INSTR' #GPIB interface number (name can be found using NI-MAX)
        psCompliance = 10.0E-6     #compliance in A
        #psCurrentRange = 1e-6    #current range in A
        psAverage = 5             #picoammeter internal measurement averaging
        #ps = Keithley2470(psID,psCompliance,psAverage)
        #ps = Keithley6517(psID,psCompliance,psAverage)
        ps = Keithley6487(psID,psCompliance,psAverage)
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
            
        #Set up LCR meter
        print('Setting up LCR meter.')
        lcrID = 'GPIB0::20::INSTR' #GPIB interface number (name can be found using NI-MAX)
        lcrFreq = 10E3            #measurement frequency in Hz
        lcrLevel = 0.1            #AC output voltage in V
        lcrAverage = 3           #LCR internal measurement averaging
        lcr = KeysightE4980AL(lcrID,lcrFreq,lcrLevel,lcrAverage)
        
        try:
            lcr.setup()
        except Exception as e:
            print (e)
            ERROR('LCR meter setup failed.')
            return 1
        print('LCR meter setup successful.')
        
        #LCR open correction
        #print("Performing lcr open correction.")
        #lcr.openCorrectionToggle('on')
        #lcr.shortCorrectionToggle('on')
        #lcr.openCorrection()
        #time.sleep(30.)
        
        
    
    
        print('Performing CV measurement using Keithley2410 and Keysight LCR.')

        ps_Vinitial = 0.         #starting HV voltage, should be 0, V
        ps_Vstart = 0.          #first measurement voltage, V
        ps_Vstep_initiate = -1.0  #Vstep used to ramp to starting voltage [ensure sign is correct]
        ps_Vfinal = -6.        #final measurement voltage, V
        ps_Vstep_run = -2.      #measurement voltage step, V [ensure sign is correct]
        rest_time = 5.          #waiting time before measurement after ramping, s
        first_point_rest_time = 15. #Additional waiting time before first voltage step, s

        psCompliance = 1E-6   #ps compliance in A
        Imax = psCompliance
        lcrFreq = [10e3, 100e3, 1000e3]         #LCR measurement frequency, Hz
        lcrLevel = 0.1         #LCR AC output voltage, V
        lcrCircuit = 'CSRS'    #LCR equivalent circuit model

        full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
        ramp_down=True      #ramp PS down to 0 V after measurement
        kill_on_hit_compliance = False #if true, measurement stops without ramping down if compliance is reached

        filenamePrefix = "Results/CV_Batch1_Wafer2_LGAD_Diced_PrA_2x2_Interpad_ProperSweep_Quick"
        
        
        #Lets retest C3 to check the bump results are real
        #Lets also check C1 to check that there is consistency with previous measurements
        #filenamePrefix = "Results/CV_Batch1_Wafer2_PiN_Diced_PoA_C3_Rerun_BumpyResultsForOneFreq"
        
        
        outputFile = str(filenamePrefix) + ".txt" #name for output data file
        pltFormatFile = []

        filesExist = False
        for f in lcrFreq:
            filename = str(filenamePrefix) + "_" + str(round(float(f)/1000)) + "kHz_plt.txt"
            pltFormatFile.append(filename)
            if os.path.isfile(filename):
                filesExist = True

        ans = "Y"
        if filesExist:
            print("Are you sure you want to overwrite these files? (Y/N)")
            
            while True:
                ans = input("Response:")
                if ans.upper() == "N":
                    print("Program will end")
                    break
                elif ans.upper() == "Y":
                    print("File will be overwritten")
                    break
                else:
                    print("Make sure your response is either a \"Y\" or a \"N\"")
         
        if ans.upper() == "Y":         
            lcr.setFrequency(lcrFreq[0])
            lcr.setLevel(lcrLevel)
            lcr.setFunctionType(lcrCircuit)
            ps.controlAverage('off')
            ps.setCompliance(psCompliance)
            ps.controlAverage('on')

            initComments = "\n";
            initComments = initComments + "Comments:" + "\n"
            initComments = initComments + "Pad only; Floating" + "\n"
            initComments = initComments + "@Start" + "\n"
            initComments = initComments + "T = +20 deg C; RH = 1.43 V" + "\n"
            initComments = initComments + "@End" + "\n"
            initComments = initComments + "T = +20 deg C; RH = 0. V" + "\n"
            initComments = initComments + "" + "\n"

            now = datetime.now()
            currentTime = now.strftime("%H:%M")
            file = open(outputFile,'w')
            file.write('Test Type: ' + test + '\n')
            file.write(currentTime+'\n')
            lcrFreq_kHz = lcrFreq[0]/1000.0
            file.write('Frequency: ' + str(lcrFreq_kHz) + 'kHz \n')
            file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
            file.write('Circuit: ' + lcrCircuit + '\n')
            file.write(initComments)
            file.close()

            for i in range(len(pltFormatFile)):
                file = open(pltFormatFile[i],'w')
                file.write('Test Type: ' + test + '\n')
                file.write(currentTime+'\n')
                lcrFreq_kHz = lcrFreq[i]/1000.0
                file.write('Frequency: ' + str(lcrFreq_kHz) + 'kHz \n')
                file.write('Amplitude: ' + str(lcrLevel) + 'V \n')
                file.write('Circuit: ' + lcrCircuit + '\n')
                file.write(initComments)
                file.close()
                


            ps_Voltages = []

            #For Testing
            #end = 50 #-50
            #for i in range(-0, end, 5): #5
            #     ps_Voltages.append(i)
            #ps_Voltages.append(end)
            
            end = -240 #-50
            for i in range(-0, end, -5): #5
                 ps_Voltages.append(i)
            ps_Voltages.append(end)
            
            #end = -50
            #for i in range(round(-0 * 10), round(end * 10), round(-0.2 * 10)):
            #    ps_Voltages.append(i / 10)
            #ps_Voltages.append(end)
            
            #end = -160
            #for i in range(-50, end, -2):
            #    ps_Voltages.append(i)
            #ps_Voltages.append(end)


            #print (ps_Voltages)

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

            #run the test
            successStatus=tests.jmMeasureCV(ps,lcr,outputFile,pltFormatFile,ps_Voltages,Imax,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time, lcrFreq)
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
            
            #Set up HV SMU
            print('Setting up HV SMU.')
            psPort = 'COM7'        #serial port to connect (port name can be found using NI-MAX)
            psCompliance = 10.0E-6  #compliance of power supply in A
            psAverage = 1         #power supply internal measurement averaging
            #ps = Keithley2410(str(psPort),psCompliance,psAverage)
            ps = Keithley6517_Serial(str(psPort),psCompliance,psAverage)
            
            
            psID = 'GPIB0::21::INSTR' #GPIB interface number (name can be found using NI-MAX)
            psCompliance = 10.0E-6     #compliance in A
            #psCurrentRange = 1e-6    #current range in A
            psAverage = 5             #picoammeter internal measurement averaging
            #ps = Keithley2470(psID,psCompliance,psAverage)
            #ps = Keithley6517(psID,psCompliance,psAverage)
            
            psID = 'GPIB0::29::INSTR' #GPIB interface number (name can be found using NI-MAX)
            psCompliance = 10.0E-6     #compliance in A
            #psCurrentRange = 1e-6    #current range in A
            psAverage = 5             #picoammeter internal measurement averaging
            #ps = Keithley2470(psID,psCompliance,psAverage)
            #ps = Keithley6517(psID,psCompliance,psAverage)
            #ps2 = Keithley6487(psID,psCompliance,psAverage)
            ps2 = None
            
            try:
                ps.setup()
                if (ps2 != None):
                    ps2.setup()
            except Exception as e:
                print (e)
                ERROR('HV SMU setup failed.')
                return 1
            current_range = psCompliance
            ps.setCurrentRange(current_range)
            ps.controlSource('on') #apply voltage
            
            if (ps2 != None):
                ps.setCurrentRange(current_range)
            print('HV SMU setup successful.')
            
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
        
            filenamePrefix = "Results/Test"
            outputFile = str(filenamePrefix) + ".txt" #name for output data file
            outputFile = 'Results/test.txt' #name for output data file
            pltFormatFile = str(filenamePrefix) + "_plt.txt"
            
            ans = "Y"
            if os.path.isfile(pltFormatFile):
                print("A file with the path: " + str(pltFormatFile) + " already exists, are you sure you want to continue? (Y/N)")
                
                while True:
                    ans = input("Response:")
                    if ans.upper() == "N":
                        print("Program will end")
                        break
                    elif ans.upper() == "Y":
                        print("File will be overwritten")
                        break
                    else:
                        print("Make sure your response is either a \"Y\" or a \"N\"")
                        
            if ans.upper() == "Y":
            
                ps.controlAverage('off')
                ps.setCompliance(psCompliance)
                ps.setCurrentRange(pow(10, psInitialCurrentRange))
                ps.controlAverage('on')

                initComments = "\n";
                initComments = initComments + "Comments:" + "\n"
                initComments = initComments + "Pad only; Floating" + "\n"
                initComments = initComments + "@Start" + "\n"
                initComments = initComments + "T = +20 deg C; RH = 0.631 V" + "\n"
                initComments = initComments + "@End" + "\n"
                initComments = initComments + "T = +20 deg C; RH = 0. V" + "\n"
                initComments = initComments + "" + "\n"

                now = datetime.now()
                currentTime = now.strftime("%H:%M")
                file = open(outputFile,'w')
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
                
                end = -150
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

    #LCI = Laser Charge Injection
    elif test=="jmLCI_test":
        #This is just a test section to try and check how the oscilloscope stuff works
        #The ip can be found by running ipconfig from command prompt
        #oscPort = 139        #serial port to connect (port name can be found using NI-MAX)
        #oscIP = '169.254.29.208'
        #osc = AgilentMSO9254A(str(oscIP), oscPort)
        
        #Some test code. It works. And now I understand a bit more
        #rm = visa.ResourceManager()
        #my_instrument = rm.get_instrument('TCPIP::169.254.29.208::139::SOCKET')
        #chamber = visa.instrument("TCPIP::169.254.29.208::139::SOCKET")
        #try:
        #    osc.setup()
        #except Exception as e:
        #    print (e)
        #    ERROR('OSC setup failed.')
        #    return 1
               
        #:CHANnel1:SCALe\s500E-3\n               
        #osc.setChannelScale(1, (500e-3)) 
               
        #osc.shutdown();
        
        #rm = visa.ResourceManager()
        #myOSC = rm.get_instrument('USB0::10893::36878;:MY53310147::0::INSTR')
        #myOSC = rm.get_instrument('USB0::0x2A8D::0x900E::MY53310147::INSTR')
        #https://pyvisa.readthedocs.io/en/1.4/pyvisa.html
        #myOSC.write(':CHANnel1:SCALe 500E-3\n')
        
        ###Above is previous iterations and tests
        
        #One of these two
        #oscVisaName = "USB0::10893::36878;:MY53310147::0::INSTR"
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"

        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
            
        #Now we setup some basic parameters for the oscilloscope.
        #Assume for now we are working with the fast amp to keep things simple
        #There is also no need to actually do this bit. We can easily just sit and read results if we want.
        #So for now we will disable this and just look into saving the current waveform
        #myOSC.setChannelScale(1, 500E-3)
        #myOSC.setChannelScale(2, 500E-3)
        
        outputFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\danMARCUScoldMicronTest"
        #outputFolder = "C:"

        #run the test
                #successStatus=tests.jmMeasureIV(ps,outputFile,ps_Voltages,Imax,psInitialCurrentRange,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time)
        successStatus = 1;
        try:    
            #This is test function where we can check how to actually save
            fileName = outputFolder+ "\\Test";
            #myOSC.setChannelScale(1, 500E-3)
            myOSC.singleMeasurement();    
            print("fileName = " + str(fileName))
            time.sleep(0.5)
            myOSC.saveWaveformXY(fileName);   
            myOSC.saveScreenGrab(fileName+".png")             
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        

    elif test=="jmLCIsweep":       
        
        print('Setting up HV SMU.')
        #psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        #psCompliance = 10.0E-6  #compliance of power supply in A
        #psAverage = 1         #power supply internal measurement averaging
        #ps = Keithley2410(str(psPort),psCompliance,psAverage)
        #ps = Keithley6517(str(psPort),psCompliance,psAverage)
            
        psPort = 'COM7'        #serial port to connect (port name can be found using NI-MAX)
        psCompliance = 10.0E-6  #compliance of power supply in A
        psAverage = 1         #power supply internal measurement averaging
        ps = Keithley2410(str(psPort),psCompliance,psAverage)
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
                
        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        myOSC.reset();
        
        #Old settings without beam monitor
        if False:
            #Setup the timebase
            myOSC.setTimeBase(10E-9, 20E-9)
            #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
            
            #Now we setup the channels 
            myOSC.setChannelSettings(1, 1, -3.5)
            myOSC.setChannelSettings(2, 0.2, -0.6)
            #myOSC.setChannelSettings(2, 20E-3, 40E-3)
            #myOSC.setChannelSettings(2, 2E-3, 6E-3)
            #myOSC.setChannelSettings(2, 10E-3, 30E-3)
            #myOSC.setChannelSettings(2, 50E-3, 150E-3)
             #
            #and the trigger
            myOSC.setTriggerEd()
            myOSC.setTriggerMode()
            myOSC.setTriggerLevel(1, -1)
        
        #New settings to include beam monitor
        if True:
            myOSC.setTimeBase(30E-9, 135E-9)
            #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
            
            #Now we setup the channels 
            myOSC.setChannelSettings(1, 1, -3.5)
            myOSC.setChannelSettings(2, 0.2, -0.6)
            myOSC.setChannelSettings(3, 0.1, 0.3)

            #and the trigger
            myOSC.setTriggerEd()
            myOSC.setTriggerMode()
            myOSC.setTriggerLevel(1, -1)
        
        #And hopefully that is all        
        print('OSC setup successful.')              
        
        
        #outputFolder = "C:\\Users\\Administrator\\Desktop\\Python Output Folder\\Laser Gain Sweeps\\"
        #outputFolder = "C:\\Users\\Administrator\\Desktop\\Python Output Folder\\Laser Gain Sweeps\\Comissioning_Tests\\"
        #outputFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Gain_Sweep_Tests\\" 
        #outputFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Gain_Sweep_TestsLHCB_SensorB_RTP_housing_ON_RH_26%_200V_11-08-22\\" #finishes %(12.4)15.6 (other 2-0.8%)
        outputFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Gain_Sweep_TestsLHCB\\" 
        #outputFolder = "C:"

        ############################### IMPORTANT ###############################
        #If you don't change this, it will just overwrite your own work. 
        #No way to check this in code at the moment
        outputFolder = outputFolder + "TCTBoard_SensorH_5%_ND0p0_AP2_6p5VAmpBias_30Repeats_m19.5_lt6.8%RH_CondOn" #finishes %(12.4)15.6 (other2-0.8%)
        
        #outputFolder = outputFolder + "TCTBoard_Wafer8_F25_FD2_10%_ND1.0_6.5VAmpBias_30Repeats_HigherRerun2"
        
        ############################### IMPORTANT ###############################
        
        ans = "Y"
        #None of that stuff makes sense. Just be careful for now
            
        if ans.upper() == "Y":
        
            rest_time = 0.25      #waiting time before measurement after ramping, s
            first_point_rest_time = 15. #Additional waiting time before first voltage step, s
            psCompliance = 10e-6
            psInitialCurrentRange = -12
            psMaxCurrentRange = -3
            Imax = psCompliance #measurement stops if measured current > Imax
            full_step=False     #if true then ramping is in one step of ps_Vstep, otherwise ramps slowly
            ramp_down=True      #ramp PS down to 0 V after measurement
            kill_on_hit_compliance = True #if true, measurement stops without ramping down if compliance is reached    
            
            #~2s per repeat
            repeats = 30
            ps_Voltages = []
        
            #For Testing
            
            ps_Voltages.append(-0)
                 
            deviceType = "LGAD"
            
            #whether to use arduino to measure conditions
            measureConditions = True
                       
            if deviceType == "LGAD":
                end1 = -80 #needs changing
                for i in range(0, end1, -2):
                    ps_Voltages.append(i)
                ps_Voltages.append(end1)
                
                
                end2 = -300 # change
                for i in range(end1, end2, -4): #change step size
                    ps_Voltages.append(i)
                ps_Voltages.append(end2)
                
                
                #ps_Voltages.append(-270)
                #ps_Voltages.append(-275)
                #ps_Voltages.append(-280)
                #end2 = -280
                
                #end3 = -305 # change
                #for i in range(end2, end3, -2): #change step size
                #    ps_Voltages.append(i)
                #ps_Voltages.append(end3)
                
            elif deviceType == "PiN":
                #(27+67) * 30 *2 = 80 minutes? 
                 
                end = -50 #needs changing
                for i in range(-0, end, -1):
                    ps_Voltages.append(i)
                ps_Voltages.append(end)
                
                
                end2 = -110 # change
                for i in range(end, end2, -1): #change step size
                    ps_Voltages.append(i)
                ps_Voltages.append(end2)
                
                # end3 = -500 # change
                # # for i in range(end2, end3, -20): #change step size
                    # # ps_Voltages.append(i)
                # # ps_Voltages.append(end3)
                
                # end4 = -560 # change
                # for i in range(end3, end4, -2): #change step size
                    # ps_Voltages.append(i)
                # ps_Voltages.append(end4)
                
            elif deviceType=="constV_TSweep":
                ps_Voltages = [-100]
                repeats=sys.maxsize
                
            elif deviceType == "ND_Sweep":
                ps_Voltages = [-0, -40, -50, -60, -70]
                
            #ps_Voltages = [-0, -40, -50, -60, -70]
                
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

            #print(old_ps_Voltages)
            #print(ps_Voltages)

            #Make a new folder and copy alignment data to it
            extraFolder = outputFolder + "\\Alignment_Data"
            if not os.path.exists(outputFolder):
                os.makedirs(extraFolder)
            
            #Copy
            alignmentFolder = "C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Alignment_Scans"
            copy_tree(alignmentFolder, extraFolder)

            successStatus = 1;
            try:            
                successStatus=tests.jmRecordPulses(myOSC, outputFolder, ps, ps_Voltages,Imax,psInitialCurrentRange,full_step,ramp_down,
                            kill_on_hit_compliance,rest_time,first_point_rest_time,repeats,measureConditions)
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

    elif test=="jmSr90HitCollection":       
        
        #print('Setting up HV SMU.')
        #psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        #psCompliance = 10.0E-6  #compliance of power supply in A
        #psAverage = 1         #power supply internal measurement averaging
        #ps = Keithley2410(str(psPort),psCompliance,psAverage)
        #ps = Keithley6517(str(psPort),psCompliance,psAverage)
            
        #psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        #psCompliance = 10.0E-6  #compliance of power supply in A
        #psAverage = 1         #power supply internal measurement averaging
        #ps = Keithley2410(str(psPort),psCompliance,psAverage)
        #try:
        #    ps.setup()
        #except Exception as e:
        #    print (e)
        #    ERROR('HV SMU setup failed.')
        #    return 1
        #current_range = psCompliance
        #ps.setCurrentRange(current_range)
        #ps.controlSource('on') #apply voltage
        #print('HV SMU setup successful.')               
                
        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        myOSC.reset();
        
        #Setup the timebase
        myOSC.setTimeBase(2E-9, 0)
        
        #myOSC.setTimeBase(20E-9, 70E-9)
        #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
        
        #Now we setup the channels 
        myOSC.setChannelSettings(1, 200E-3, 600E-3) #For two stage amps
        
        #myOSC.setChannelSettings(1, 200E-3, 0E-3) #For two stage amps
        #myOSC.setChannelSettings(1, 20E-3, 60E-3) #For just first amps
        #myOSC.setChannelSettings(1, 10E-3, -20E-3) #For two stage amps

        myOSC.setChannelSettings(2, 200E-3, 400E-3) #For two stage amps
        
        #myOSC.setChannelSettings(2, 200E-3, 0E-3) #For two stage amps
        #myOSC.setChannelSettings(2, 20E-3, 40E-3) #For just first amps

         #
        #and the trigger
        myOSC.setTriggerEd()
        myOSC.setTriggerMode()

        trigChannel = 1
        myOSC.setTriggerLevel(trigChannel, 50E-3) #For two stage amps
        #myOSC.setTriggerLevel(trigChannel, 50E-3) #For two stage amps
        #myOSC.setTriggerLevel(trigChannel, 5E-3) #For just first amps
        
        #And hopefully that is all        
        print('OSC setup successful.')              
        
        
        #outputFolder = "C:\\Users\\Administrator\\Desktop\\Python Output Folder\\Amplifier Tests\\"
        outputFolder = "D:\\"
        #outputFolder = "E:"
        #outputFolder = "C:\\"

        ############################### IMPORTANT ###############################
        #If you don't change this, it will just overwrite your own work. 
        #No way to check this in code at the moment
        #outputFolder = outputFolder + "Run10_SCTB_VBias175V_4mm_PrA_LGAD_SameTwoDevices_BothAmps_2ndStage8.0VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "Run11_SCTB_Top-Bot_VBias430V-240V_4mm_PrA_LGAD_W21-W2_BothAmps_2ndStage8.5-6.5VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "Run12_SCTB_Top-Bot_VBias460V-240V_4mm_PrA_LGAD_W21-W2_BothAmps_2ndStage7.5-6.5VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "SCTB_PiN_4mm_PoA_FA_40%_1320mV_50Hz_ND2.0_BothAmps"
        
        #outputFolder = outputFolder + "AmpTest_BOT_6.5VBias_SqrWave_10MHz_10mVp2p_5mVOffset_40%DC_5mVTrigger_SignalOnly"
        #outputFolder = outputFolder + "AmpTest_BOT_6.5VBias_SqrWave_10MHz_10mVp2p_5mVOffset_40%DC_5mVTrigger_WithAmp"
        
        #outputFolder = outputFolder + "SCTB_W2_TEST_6.5VAmpBias_Vbias240V"
        #outputFolder = outputFolder + "Run14_SCTB_Top-Bot_180VBias_W3_F7-F25_S1_FD1_BothAmps_2ndStage6.5-6.5VBias_50mVTrigger"
        #outputFolder = outputFolder + "Irradiated_Run"
        
        #outputFolder = outputFolder + "Run15_SCTB_Top-Bot_160VBias_W3_F16-F17_S1_FA2-FB1_BothAmps_2ndStage6.5-6.5VBias_50mVTrigger"
        #outputFolder = outputFolder + "Run15_SCTB_Top-Bot_160VBias_W3_F16-F17_S1_FC2-FB1_BothAmps_2ndStage6.5-6.5VBias_50mVTrigger"
        #outputFolder = outputFolder + "Run15_SCTB_Top-Bot_160VBias_W3_F16-F16_S1_FA2-FC2_BothAmps_2ndStage6.5-6.5VBias_50mVTrigger"
        #outputFolder = outputFolder + "Run15_SCTB_Top-Bot_160VBias_W3_F16-F16_S1_FC2-FA2_BothAmps_2ndStage6.5-6.5VBias_50mVTrigger"
        
        #outputFolder = outputFolder + "Run16_SCTB_Top_PiN_150VBias_50mVTrigger"
        
        outputFolder = outputFolder + "Run17_SCTB_Top-Bot_VBias160V-sweep_W3_W6_420Repeat_Extra"
        
        ############################### IMPORTANT ###############################
        
        ans = "Y"
        #None of that stuff makes sense. Just be careful for now
            
        if ans.upper() == "Y":
        
            runTime = -1
            #^Run forever
            
            successStatus = 1;
            try:            
                successStatus=tests.jmCollectHits(myOSC, outputFolder, runTime)
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
            
    elif test=="jmSr90HitCollection_Fixed":       
        
        #print('Setting up HV SMU.')
        #psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        #psCompliance = 10.0E-6  #compliance of power supply in A
        #psAverage = 1         #power supply internal measurement averaging
        #ps = Keithley2410(str(psPort),psCompliance,psAverage)
        #ps = Keithley6517(str(psPort),psCompliance,psAverage)
            
        #psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        #psCompliance = 10.0E-6  #compliance of power supply in A
        #psAverage = 1         #power supply internal measurement averaging
        #ps = Keithley2410(str(psPort),psCompliance,psAverage)
        #try:
        #    ps.setup()
        #except Exception as e:
        #    print (e)
        #    ERROR('HV SMU setup failed.')
        #    return 1
        #current_range = psCompliance
        #ps.setCurrentRange(current_range)
        #ps.controlSource('on') #apply voltage
        #print('HV SMU setup successful.')               
           
        psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        psCompliance = 10.0E-6  #compliance of power supply in A
        psAverage = 1         #power supply internal measurement averaging
        ps = Keithley2410(str(psPort),psCompliance,psAverage)
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
           
        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        myOSC.reset();
        
        #Setup the timebase
        myOSC.setTimeBase(2E-9, 0)
        #myOSC.setTimeBase(20E-9, 70E-9)
        #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
        
        #Now we setup the channels 
        myOSC.setChannelSettings(1, 200E-3, 600E-3) #For two stage amps
        #myOSC.setChannelSettings(1, 20E-3, 60E-3) #For just first amps
        #myOSC.setChannelSettings(1, 10E-3, -20E-3) #For two stage amps

        myOSC.setChannelSettings(2, 200E-3, 400E-3) #For two stage amps
        #myOSC.setChannelSettings(2, 20E-3, 40E-3) #For just first amps

         #
        #and the trigger
        myOSC.setTriggerEd()
        myOSC.setTriggerMode()

        trigChannel = 1
        myOSC.setTriggerLevel(trigChannel, 50E-3) #For two stage amps
        #myOSC.setTriggerLevel(trigChannel, 50E-3) #For two stage amps
        #myOSC.setTriggerLevel(trigChannel, 5E-3) #For just first amps
        
        #And hopefully that is all        
        print('OSC setup successful.')              
        
        
        #outputFolder = "C:\\Users\\Administrator\\Desktop\\Python Output Folder\\Amplifier Tests\\"
        outputFolder = "D:\\"
        #outputFolder = "E:"
        #outputFolder = "C:\\"

        ############################### IMPORTANT ###############################
        #If you don't change this, it will just overwrite your own work. 
        #No way to check this in code at the moment
        #outputFolder = outputFolder + "Run10_SCTB_VBias175V_4mm_PrA_LGAD_SameTwoDevices_BothAmps_2ndStage8.0VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "Run11_SCTB_Top-Bot_VBias430V-240V_4mm_PrA_LGAD_W21-W2_BothAmps_2ndStage8.5-6.5VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "Run12_SCTB_Top-Bot_VBias460V-240V_4mm_PrA_LGAD_W21-W2_BothAmps_2ndStage7.5-6.5VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "SCTB_PiN_4mm_PoA_FA_40%_1320mV_50Hz_ND2.0_BothAmps"
        
        #outputFolder = outputFolder + "AmpTest_BOT_6.5VBias_SqrWave_10MHz_10mVp2p_5mVOffset_40%DC_5mVTrigger_SignalOnly"
        #outputFolder = outputFolder + "AmpTest_BOT_6.5VBias_SqrWave_10MHz_10mVp2p_5mVOffset_40%DC_5mVTrigger_WithAmp"
        
        outputFolder = outputFolder + "Run20_SCTB_Top-Bot_VBias160V-sweep_W3_W11"
        ############################### IMPORTANT ###############################
        
        #ps_Voltages = [-150, -150, -150, -155, -160, -165, -170, -175, -180, -185, -190]
        
        #ps_Voltages = [-110, -115, -120, -125, -130, -135, -140, -145, -150]
        #ps_Voltages = [-150, -200, -250, -270, -280, -290, -300] 
        #ps_Voltages = [-250, -300, -350, -400, -410, -420, -430, -435] 
        ps_Voltages = [-400, -420, -440, -460, -480] 
        #Running the same voltage multiple times means that we can get higher statistics for the voltages we care about
        
        ans = "Y"
        #None of that stuff makes sense. Just be careful for now
            
        if ans.upper() == "Y":
        
            #3.3hrs
            #12000 seconds
            #runTime = 12000
            
            #9hrs
            #runTime = 32400
            
            #8hrs
            runTime = 28800
            
            #6hrs
            #runTime = 21600
            
            #4hrs
            #runTime = 14400
            
            #runTime = -1 #Run forever
            
            successStatus = 1;
            try:            
                successStatus=tests.jmCollectHits_Fixed(myOSC, ps, ps_Voltages, outputFolder, runTime)
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
            
            
    elif test=="jmPwrSupplyRamp":                        
                
        print('Setting up Power Supply')
        psPort = 'COM8'        #serial port to connect (port name can be found using NI-MAX)
        psCompliance = 10.0E-6  #compliance of power supply in A
        psAverage = 1         #power supply internal measurement averaging
        ps = MX180TP(str(psPort),psCompliance,psAverage)
        try:
            ps.setup()
        except Exception as e:
            print (e)
            ERROR('Power Supply setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        ps.reset();
        
        #Setup the Voltage as a test
        #ps.setTimeBase(2E-9, 0)
        #ps.setVoltage(1, 2.63)
        #ps.setCurrentLimit(1, 0.15)
        
        #Now the initial values. We'll set the current limit to a constant 250mA while the voltage
        #can just start at 0. We will also begin measurments 
        ps.setVoltage(1, 0)
        ps.setCurrentLimit(1, 0.25)
        ps.controlSource(1, 'on')
        
        #And hopefully that is all        
        print('Power Supply setup successful.')              
        
        
        #outputFolder = "C:\\Users\\Administrator\\Desktop\\Python Output Folder\\Amplifier Tests\\"
        #outputFolder = "D:"
        #outputFolder = "E:"
        outputFolder = "C:"

        ############################### IMPORTANT ###############################
        #If you don't change this, it will just overwrite your own work. 
        #No way to check this in code at the moment
        #outputFolder = outputFolder + "Run10_SCTB_VBias175V_4mm_PrA_LGAD_SameTwoDevices_BothAmps_2ndStage8.0VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "Run11_SCTB_Top-Bot_VBias430V-240V_4mm_PrA_LGAD_W21-W2_BothAmps_2ndStage8.5-6.5VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "Run12_SCTB_Top-Bot_VBias460V-240V_4mm_PrA_LGAD_W21-W2_BothAmps_2ndStage7.5-6.5VBias_50mVTrigger_NewSource"
        #outputFolder = outputFolder + "SCTB_PiN_4mm_PoA_FA_40%_1320mV_50Hz_ND2.0_BothAmps"
        
        #outputFolder = outputFolder + "AmpTest_BOT_6.5VBias_SqrWave_10MHz_10mVp2p_5mVOffset_40%DC_5mVTrigger_SignalOnly"
        #outputFolder = outputFolder + "AmpTest_BOT_6.5VBias_SqrWave_10MHz_10mVp2p_5mVOffset_40%DC_5mVTrigger_WithAmp"
        
        outputFolder = outputFolder + "NewScope_Test1"
        ############################### IMPORTANT ###############################
        
        ans = "Y"
        #None of that stuff makes sense. Just be careful for now
            
        if ans.upper() == "Y":
        
            runTime = -1
            #^Run forever
            
            successStatus = 1;
            try:            
                bump = True
                #successStatus=tests.jmCollectHits(myOSC, outputFolder, runTime)
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

    #LCI = Laser Charge Injection
    elif test=="jmHumidTest":
        #This is just a test section to try and check how the oscilloscope stuff works

        print("Testing Humidity")

        ser = serial.Serial(port='COM10', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        print("Serial Port Setup",ser)
    
        try:               
            count = 1
            fullLine = ""
            print("Ready to start reading")
            fullLine = ""
            seq = []
            while True:
                #print("gET HERE 1")
                #print(ser.read())
                if True:
                    #print("gET HERE 2")
                    #print("Serial Port read",ser)
                    #print(len(ser.read()))
                    for c in ser.read():
                        #print("gET HERE 3")
                        seq.append(chr(c))
                        joined_seq = ''.join(str(v) for v in seq)
                        #print(c, chr(c), str(chr(c)))
                        #fullLine = fullLine + str(chr(c))
                        if c == '10' or chr(c) == '\n':  
                            #print("End Line Found")                        
                            print(str(joined_seq))
                            #fullLine = ""
                            seq = []
                            break
                        #print(str(count) + str(": ") + chr(line))
                        #count = count + 1
                    #if not fullLine == "":
                        #ser.flush()
                        #print(str(count) + str(": ") + str(fullLine))
                        #print(str(fullLine))
                        #count = count + 1
                        #time.sleep(0.5)
                if False:
                    line = ser.readline()
                    print(str(line)[2:][:-5])
                
            
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
                
    elif test=="jmXCtest":
    
        XlC = XilabController()

        try:
            XlC.setup()
        except Exception as e:
            print (e)
            ERROR('Xilab Controller setup failed.')
            return 1

        #print("XlC.deviceID_1 = " + str(XlC.deviceID_1))
        
        print('')
        print('Initialising Stage')  
      
        print('')
        print('Setting micro step mode (256)')
        XlC.set_microstep_mode_256(XlC.deviceID_1)
        XlC.set_microstep_mode_256(XlC.deviceID_2)
        XlC.set_microstep_mode_256(XlC.deviceID_3)        
        
        print('')
        print('Zero device 1 (x)')
        startpos, ustartpos = XlC.get_position(XlC.deviceID_1)      
        print('')
        print('Zeroing')
        XlC.set_zero_pos(XlC.deviceID_1)        
        startpos, ustartpos = XlC.get_position(XlC.deviceID_1)
        
        print('')
        print('Zero device 2 (y)')
        startpos, ustartpos = XlC.get_position(XlC.deviceID_2)      
        print('')
        print('Zeroing')
        XlC.set_zero_pos(XlC.deviceID_2)        
        startpos, ustartpos = XlC.get_position(XlC.deviceID_2)
      
        #We don't do the z direction as we want to keep that constant.
        #We could implement it, but it shouldn't be a neccessity
      
        #Now we have some demo code showing how to move things about
      
        print('')
        print('Testing Movement (x)')
        if False:
            #Basic test showing all of the steps manually using the original functions            
            startpos, ustartpos = XlC.get_position(XlC.deviceID_1)
            steps, usteps = XlC.calc_steps(-100)
            print('')
            XlC.move_to(XlC.deviceID_1, steps, usteps)
            XlC.wait_for_stop(XlC.deviceID_1, 100)
            startpos, ustartpos = XlC.get_position(XlC.deviceID_1)
      
        if False:
            #Streamlined the move command to just one function taking the microns as the input
            #Other functions are just to check position etc. 
            XlC.get_position(XlC.deviceID_1)
            XlC.move_to_microns(XlC.deviceID_1, -1000)
            XlC.wait_for_stop(XlC.deviceID_1, 100)
            XlC.get_position(XlC.deviceID_1)
            
        if True:
            #Demonstrating the return home command
            XlC.get_position(XlC.deviceID_1)
            XlC.move_to_microns(XlC.deviceID_1, -5000)
            XlC.wait_for_stop(XlC.deviceID_1, 100)
            XlC.get_position(XlC.deviceID_1)
            XlC.return_home(XlC.deviceID_1)
            XlC.wait_for_stop(XlC.deviceID_1, 100)
            XlC.get_position(XlC.deviceID_1)
            
        if False:
            #Demonstrating the return home command
            XlC.get_position(XlC.deviceID_2)
            XlC.move_to_microns(XlC.deviceID_2, -1000)
            XlC.wait_for_stop(XlC.deviceID_2, 100)
            XlC.get_position(XlC.deviceID_2)
            XlC.return_home(XlC.deviceID_2)
            XlC.wait_for_stop(XlC.deviceID_2, 100)
            XlC.get_position(XlC.deviceID_2)
            
        print('')
        print('Testing Movement Over')
            
        print('')
        print('Xilab Controller setup successful.')   






    elif test=="jmLaserAlignment":
    
        print('')
        print('')
        print('Laser Alignment Test Selected - A few useful notes:')
        print('Make sure the Laser is turned on with a sufficently high power (>=50%)')
        print('The beam monitor can only work with Laser powers <=35%')
        print('Make sure the sensor is sufficently biased and the amplifier is also powered')
        print('')
        print('')
    
        #For example (known with Te2v Wafer 2 PrA 1mm LGADs)
        #150V Bias, 6.5V AmpBias, 35% Laser Power. Gives an amplitude of around 80mV with noise down at 20mV. 
        #So you could set a threshold to 50mV (and check for positive overshoots too)
        
        #For a PiN, you want a little different.
        #So 10% power, 150V bias.
    
        XlC = XilabController()

        try:
            XlC.setup()
        except Exception as e:
            print (e)
            ERROR('Xilab Controller setup failed.')
            return 1

        #print("XlC.deviceID_1 = " + str(XlC.deviceID_1))
        
        print('')
        print('Initialising Stage')  
      
        print('')
        #print('Setting micro step mode (256)')
        XlC.set_microstep_mode_256(XlC.deviceID_1)
        XlC.set_microstep_mode_256(XlC.deviceID_2)
        XlC.set_microstep_mode_256(XlC.deviceID_3)        
        
        #print('')
        #print('Zero device 1 (x)')
        #startpos, ustartpos = XlC.get_position(XlC.deviceID_1)      
        #print('')
        #print('Zeroing')
        XlC.set_zero_pos(XlC.deviceID_1)        
        #startpos, ustartpos = XlC.get_position(XlC.deviceID_1)
        
        #print('')
        #print('Zero device 2 (y)')
        #startpos, ustartpos = XlC.get_position(XlC.deviceID_2)      
        #print('')
        #print('Zeroing')
        XlC.set_zero_pos(XlC.deviceID_2)        
        #startpos, ustartpos = XlC.get_position(XlC.deviceID_2)
        print('Xilab Controller setup successful.')

        print('')

        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        myOSC.reset();
        
        #Setup the timebase
        myOSC.setTimeBase(30E-9, 135E-9)
        #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
        
        #Now we setup the channels 
        myOSC.setChannelSettings(1, 1, -3.5)
        myOSC.setChannelSettings(2, 0.2, -0.6)
        myOSC.setChannelSettings(3, 0.1, 0.3)

        #and the trigger
        myOSC.setTriggerEd()
        myOSC.setTriggerMode()
        myOSC.setTriggerLevel(1, -1)
        
        #And hopefully that is all        
        print('OSC setup successful.')   

        print('')
        
        outputFolder = "C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Waveforms\\Test"
        linkedFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Waveforms\\Test"
         
        scanFolder = "C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Alignment_Scans"
        scanFileName = "TestScanNDD"
        
        """
        successStatus = 1;        
        try:            
            successStatus=tests.jmSpiralSearch(XlC, myOSC, linkedFolder, outputFolder)
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)                
            
        
        successStatus2 = 1;
        if successStatus == 0:
            try:            
                #successStatus2=tests.jmFineSearch1D(XlC, myOSC, linkedFolder, outputFolder, scanFolder, scanFileName, XlC.deviceID_1)
                successStatus2=tests.jmFineSearch2Dx2(XlC, myOSC, linkedFolder, outputFolder, scanFolder)
            except KeyboardInterrupt:
                print('Interrupted')
                try:
                    sys.exit(0)
                except SystemExit:
                    os._exit(0)  
                
        if successStatus==0 and successStatus2==0:
            print("Successfull test")
        else: 
            print("Test failed, see above")
            
        """
        
        successStatus = 1;
        try:            
            #successStatus2=tests.jmFineSearch1D(XlC, myOSC, linkedFolder, outputFolder, scanFolder, scanFileName, XlC.deviceID_1)
            successStatus=tests.jmFineSearch2Dx2(XlC, myOSC, linkedFolder, outputFolder, scanFolder)
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
         
         
    elif test=="jmBeamMonitor_Fixed":          

        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        myOSC.reset();
        
        #Setup the timebase
        myOSC.setTimeBase(30E-9, 135E-9)
        #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
        
        #Now we setup the channels 
        myOSC.setChannelSettings(1, 1, -3.5)
        myOSC.setChannelSettings(2, 0.2, -0.6)
        myOSC.setChannelSettings(3, 0.1, 0.3)

        #and the trigger
        myOSC.setTriggerEd()
        myOSC.setTriggerMode()
        myOSC.setTriggerLevel(1, -1)
        
        #And hopefully that is all        
        print('OSC setup successful.')   

        print('')
        
        outputFolder = "C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Beam_Monitor_Tests"
        linkedFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Beam_Monitor_Tests"
        
        fileName = "2022_03_25__10_26_20min_Run_40%_1320mV_50Hz_6500mVAmpBias_NoSensor"
        #fileName = "Test"
        
        successStatus = 1;        
        try:            
            successStatus=tests.jmBeamMonitoring(myOSC, linkedFolder, outputFolder, fileName)
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
         
         
         
    elif test=="jmTimingEfficiency":
        
        #Initial User Defined Variables
        runTime = 5 * 60 #s
        
        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        myOSC.reset();
        
        #Setup the timebase
        myOSC.setTimeBase(2E-9, 0)

        #Now we setup the channels 
        myOSC.setChannelSettings(1, 200E-3, 600E-3) #For two stage amps
        myOSC.setChannelSettings(2, 200E-3, 400E-3) #For two stage amps

        #and the trigger
        myOSC.setTriggerEd()
        myOSC.setTriggerMode()

        trigChannel = 1
        myOSC.setTriggerLevel(trigChannel, 50E-3) #For two stage amps  #was 80mV
        
        #And hopefully that is all        
        print('OSC setup successful.')              

        print('')
        
        outputFolder = "C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Timing_Efficiency_Tests"
        linkedFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Timing_Efficiency_Tests"
        
        fileName = "Test_Waveform"
        
        successStatus = 1;        
        try:            
            successStatus=tests.jmTimingEfficiency(myOSC, linkedFolder, outputFolder, fileName, runTime)
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
         
    
    elif test == 'mmFull2DScan':
        """
        Assume that jmLaserAlignment has already been run and we're probably near somewhere in the middle of the sensor (0, 0)u
        from here, go to the top left corner (2500, 250)u and do a test every 5u each way (chaosscan does this)
        """
        #set up xilab
        XlC = XilabController()

        try:
            XlC.setup()
        except Exception as e:
            print (e)
            ERROR('Xilab Controller setup failed.')
            return 1
        
        print('')
        print('Initialising Stage')  
      
        print('')
        #print('Setting micro step mode (256)')
        XlC.set_microstep_mode_256(XlC.deviceID_1)
        XlC.set_microstep_mode_256(XlC.deviceID_2)
        XlC.set_microstep_mode_256(XlC.deviceID_3)        
        
        #set zero positions as current positions
        XlC.set_zero_pos(XlC.deviceID_1)        
        XlC.set_zero_pos(XlC.deviceID_2)        
        print('Xilab Controller setup successful.')

        print('')

        print('Setting up OSC.')
        oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"
        myOSC = AgilentMSO9254A(oscVisaName)
        try:
            myOSC.setup()
        except Exception as e:
            print (e)
            ERROR('OSC setup failed.')
            return 1
                       
        #We now need to do some setup for the Osc to make sure it works and is setup properly
        
        #We start with a reset to set everything back to default
        myOSC.reset();
        
        #Setup the timebase
        myOSC.setTimeBase(30E-9, 135E-9)
        #Was 20ns, 40ns but the pulse is a lot faster with this new amp etc
        
        #Now we setup the channels 
        myOSC.setChannelSettings(1, 1, -3.5)
        myOSC.setChannelSettings(2, 0.2, -0.6)
        myOSC.setChannelSettings(3, 0.1, 0.3)

        #and the trigger
        myOSC.setTriggerEd()
        myOSC.setTriggerMode()
        myOSC.setTriggerLevel(1, -1)
        
        #And hopefully that is all        
        print('OSC setup successful.')   

        print('')
        
        #
        outputFolder = "C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Waveforms\\mmTest"
        linkedFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\Waveforms\\mmTest"



        #generate coordinates to be tested
        step = 5   #vary the granularity of the test (make this a factor of the grid size)
        #below sets the size of the grid in microns we want to test (around (0, 0))
        
        x_range = np.arange(-250, 250+step, step)
        y_range = np.arange(-250, 250+step, step)

        coords = list(itertools.product(x_range, y_range))
        #coords is a list of coords we want to test at
        print("you are testing")
        print(coords)
        #print(len(coords))

        #send to testfunction, that runs the test and takes a while
        output_coords, integrals, heights = tests.mmChaosSearch(XlC, myOSC, linkedFolder, outputFolder, coords)
        
        #can just use coords instead of output coords but im worried about them being in the wrong order (deffo wont be tho im sure)
        #had to switch to just using coords now that averaging is included in the testfunction
        #write to file #NoTE IT WILL JUST APPEND TO THE SAME FILE ATM
        with open('C:\\Users\\bilpa_login\\Desktop\\LGAD_Project\\Oscilloscope_Data\\Waveforms\\results.txt', 'a') as file:
                for i in range(0, len(integrals)):
                    file.write(f'{coords[i][0]},{coords[i][1]},{integrals[i]},{heights[i]}\n')
                    #x, y, integrals
        
        #hopefully should be able to just access results.txt and plt.imshow it or something!

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
