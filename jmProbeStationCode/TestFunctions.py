#!/usr/bin/python
# MeasurementFunctions.py -- contains classes for running IV and CV tests
# Updated: 05/03/2021
# Contributing: Matt Basso (University of Toronto), Tim Knight (University of Toronto), Will George (University of Birmingham)

import sys, os, time
from Read_Write_Files.Read_FastOsc_Output import Read_XYFormat
from Read_Write_Files.Write_Plt_Format import  Write_StandardPltFormat
from Read_Write_Files.Write_Plt_Format import  Read_StandardPltFormat
from Mathematical_Analysis.Interpolation import linearInterpolation_2pT
from Sorting_Algorithms.MultidimentionalArraySort import d2SortX

from Plots import IVTimePlot as TimePlot
from Plots import TwoIVPlotWindow as MD8TimePlot
from Plots import IVPlotWindow
from Plots import CVPlotWindow

from math import fabs
import numpy as np
import math
from matplotlib.pyplot import ion, draw
import matplotlib.pyplot as plotter 

from colorama import Fore, Style

def WARNING(message):
    print(Fore.YELLOW + '[WARNING]' + Style.RESET_ALL + '$ {}'.format(message))

def ERROR(message):
    print(Fore.RED + '[ERROR]' + Style.RESET_ALL + '$ {}'.format(message))

def raiseError(message):
    ERROR(message)
    raise ValueError(message)
    
def STATUS(message, success):
    if success:
        print(Fore.GREEN + '[STATUS]' + Style.RESET_ALL + '$ {}'.format(message))
    else:
        print(Fore.RED + '[STATUS]' + Style.RESET_ALL + '$ {}'.format(message))
        
        
def RampDown(ps,rampDownStep,rampDownWait):

    currentVoltage=(float)(ps.readVoltageAndCurrent()[0])
    nSteps=fabs(currentVoltage)/rampDownStep
    
    if currentVoltage>=0: 
        rampDownStep=-1*fabs(rampDownStep)
    else:
        rampDownStep=fabs(rampDownStep)
        
    for i in range(0,(int)(nSteps)):
        currentVoltage+=rampDownStep
        print("Ramping: " + str(currentVoltage) + "V")
        ps.setVoltage(currentVoltage)
        ps.triggerRead()
        time.sleep(rampDownWait)
        
    #should now be within 1 step of 0V, now set it exactly to 0V
    ps.setVoltage(0.0)
    ps.triggerRead()
    ps.controlSource('off')


def RampVoltage(ps,start,end,step):
      
    successfulRamp=True
    
    voltageTolerance=0.01 #V
    rest_time=5
    
    if end>=start:
        step=fabs(step)
    else:  
        step=-1*fabs(step)
    
    try:
        print("Performing voltage ramp between",start,"and",end,"V")
        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        if fabs(start-voltageCheck)>voltageTolerance:
            print("Voltage ramp target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck,", aborting run")
            raiseError("HV bias error")

        for targetVoltage in np.arange(start,end+step,step):
            print("Stepping HV bias to",targetVoltage,"V")
            #set voltage, check we don't hit compliance
            ps.setVoltage(targetVoltage)
            
            print("Checking compliance")
            if ps.hitCompliance(5):
                raiseError("supply has hit compliance at voltage:{} aborting run".format(targetVoltage))
            
            time.sleep(rest_time)

            #perform measurement
            voltage, current = ps.readVoltageAndCurrent()

            #check voltage makes sense
            if fabs(targetVoltage-voltage)>voltageTolerance:
                print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                raiseError("Measured voltage does not match that observed, aborting run")
                      
            
    except Exception as e:
        print(e)
        successfulRamp=False       
    
    return successfulRamp        

def RampUp(ps,targetVoltage):
      
    successfulRamp=True
    
    voltageTolerance=0.01 #V
    rest_time=0.25 #5
    step = 2 #V    
    
    try:
        print("Performing voltage ramp to "+ str(targetVoltage) + "V")
        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        
        #Check the target is bigger than the current voltage
        if voltageCheck < targetVoltage:
            print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
            raiseError("Measured voltage is larger than the voltage you are trying to ramp to!")
                
        currentVoltage = voltageCheck
        ramping = True
        while (ramping):
            
            #Firstly check if we are within range
            distance = fabs(targetVoltage - currentVoltage)
            
            newVoltage = 0            
            if (distance <= step):
                newVoltage = targetVoltage
                ramping = False
            else:
                newVoltage = currentVoltage - step # - because reverse bias for a negative number
                        
            print("Stepping HV bias to",newVoltage,"V")
            #set voltage, check we don't hit compliance            
            ps.setVoltage(newVoltage)
            
            currentVoltage = newVoltage
                        
            print("Checking compliance")
            if ps.hitCompliance(5):
                raiseError("supply has hit compliance at voltage:{} aborting run".format(targetVoltage))
            
            time.sleep(rest_time)

            #perform measurement
            voltage, current = ps.readVoltageAndCurrent()

            #check voltage makes sense
            if fabs(newVoltage-float(voltage))>voltageTolerance:
                print("Target voltage:",newVoltage,"Measured  voltage=", voltage)
                raiseError("Measured voltage does not match that observed, aborting run")
                      
            
    except Exception as e:
        print(e)
        successfulRamp=False   
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_type, exc_tb.tb_lineno)        
    
    return successfulRamp   
    

def threadingTestFunction(frame):  
    while frame.abortTest==False:
        print("I am still running, abort test=",frame.abortTest)
        time.sleep(1)
    print("Run aborted")  
    frame.b_run.Enable()
    


if __name__ == '__main__':
    pass


def jmMeasureCV(ps,lcr,save_path,pltFormatFile,Voltages,Imax,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time, lcrFrequencies):
    # Peform CV test using power supply, ps, and lcr meter, lcr. 
   
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V 1.0
    rampDownWait=0.25 #s 0.5
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    
    #Setdata file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time Voltage(V) Current(A) Capacitance(F) Resistance(Ohm) Frequency (kHz)\n')
    print('{0} created successfully...'.format(save_path))

    #Alternate Saving Path
    pltData = []
    
    for i in range(len(pltFormatFile)):
        pltData.append(open(pltFormatFile[i], 'a'))
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
        pltData[i].write('PS Voltage(V) PS Current(A) #Date-Time\n')
        pltData[i].write('x,y\n')

    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = CVPlotWindow()
    plot.open()
    #plotC2 = CVPlotWindow()
    #plotC2.open()
    
    print("Setup complete- beginning test")
    comment = ""

    try:

        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        #if fabs(float(Vstart)-float(voltageCheck))>float(voltageTolerance):
        #    print("Target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck)
        #    comment = "Initial voltage did not match that requested, aborting"
        #    raiseError("Initial voltage did not match that requested, aborting")
        if fabs(Voltages[0]-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",Voltages[0],"Measured starting voltage=", voltageCheck)
            comment = "Initial voltage did not match that requested, aborting"
            raiseError("Initial voltage did not match that requested, aborting")
                  
        #print(Vstart,Vfinal,Vstep_run)
        print(min(Voltages),max(Voltages))
        #for targetVoltage in np.arange(Vstart,Vfinal+Vstep_run,Vstep_run):
        index = -1
        while index < len(Voltages) - 1:              
            index = index + 1
            print("")
            print("index = " + str(index) + "  (" + str(index+1) + " / " + str(len(Voltages)) + ")")
            targetVoltage = Voltages[index]
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            ps.setVoltage(targetVoltage)
            print("Checking compliance")
            if ps.hitCompliance(5):
                comment = "PS has hit compliance at voltage:{} aborting run".format(targetVoltage)
                raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))

            time.sleep(rest_time)
            
            #begin measurement
            for i in range(len(lcrFrequencies)):
                frequency = lcrFrequencies[i]
            #for frequency in lcrFrequencies:
            
                #set LCR frequency
                lcr.setFrequency(frequency)
                time.sleep(0.5) #wait to make sure frequency has been updated?
                voltage, current = ps.readVoltageAndCurrent()
                capacitance = lcr.readCapacitance()
                resistance = lcr.readResistance()
                
                #check voltage makes sense
                if fabs(float(targetVoltage)-float(voltage))>float(voltageTolerance):
                    comment = "Measured voltage does not match that observed, aborting run"
                    print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                    raiseError("Measured voltage does not match that observed, aborting run")
                
               #check current makes sense
                if float(current)>Imax:
                    print("Maximum current:",Imax,"Measured  current=", current)
                    raiseError("Measured current exceeds max requested, aborting run")
               
                date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
                measurement = [date_time, voltage, current, capacitance, resistance, (str)(frequency/1000.0)]
                measurement = [(str)(x) for x in measurement]
                measurement2 = [date_time, voltage, current, 1 / float(capacitance) / float(capacitance), resistance, (str)(frequency/1000.0)]
                measurement2 = [(str)(x) for x in measurement2]
                data.write(' '.join(measurement) + '\n')
                
                pltData[i].write(str(float(voltage)) + ',' + str(1 / float(capacitance) / float(capacitance)) + ",   " + date_time + ",   " + comment + '\n')
                
                plot.update(measurement)
                #plotC2.update(measurement2)
                print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

                comment = ""
     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    ps.controlSource('off')
    #save plots
    print('Saving CV plots...')
    plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    #plotC2.mainplt.savefig('{0}/C2V_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    #plotC2.close()
    
    for i in range(len(pltData)):
        pltData[i].close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status

def jmRecordPulses(myOSC, save_folder,ps,Voltages,Imax,InitCurrentRange,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time,repeats):
    #So some assumptions for this test measurement:
    #That the oscilloscope is setup auto triggering and all your settings are as you want them
    #All we need to do is set to single trigger mode
    #Trigger
    #Record the data
    #Move onto next voltage (but for now we will just test the saving aspect
    
    
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    currentCurrentRange = InitCurrentRange
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    try:
    
        #One of the first tings we will do is to make the relevant directories 
        #(I don't think it overwrites anything, but we are only doing this once 
        #at the start anyway
        #We have to do each folder separately
        myOSC.mkdir(save_folder)
        myOSC.mkdir(save_folder + '\\Data\\')
        myOSC.mkdir(save_folder + '\\Images\\')

        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        #if fabs(float(Vstart)-float(voltageCheck))>float(voltageTolerance):
        #    print("Target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck)
        #    comment = "Initial voltage did not match that requested, aborting"
        #    raiseError("Initial voltage did not match that requested, aborting")
        #if fabs(Voltages[0]-voltageCheck)>voltageTolerance:
        if fabs(0-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",Voltages[0],"Measured starting voltage=", voltageCheck)
            comment = "Initial voltage did not match that requested, aborting"
            raiseError("Initial voltage did not match that requested, aborting")
                  
        #print(Vstart,Vfinal,Vstep_run)
        print(min(Voltages),max(Voltages))
        #for targetVoltage in np.arange(Vstart,Vfinal+Vstep_run,Vstep_run):
        index = -1
        
        while index < len(Voltages) - 1:              
            index = index + 1
            print("")
            print("index = " + str(index) + "  (" + str(index+1) + " / " + str(len(Voltages)) + ")")
            targetVoltage = Voltages[index]
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            RampUp(ps, targetVoltage)
            #ps.setVoltage(targetVoltage)
            print("Checking compliance")
            #if ps.hitCompliance(5):
                #comment = "PS has hit compliance at voltage:{} aborting run".format(targetVoltage)
                #raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))

            time.sleep(rest_time)
            voltage, current = ps.readVoltageAndCurrent()
            
            #check voltage makes sense
            if fabs(float(targetVoltage)-float(voltage))>float(voltageTolerance):
                comment = "Measured voltage does not match that observed, aborting run"
                print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                raiseError("Measured voltage does not match that observed, aborting run")
            
           #check current makes sense
            #if float(current)>Imax:
                #print("Maximum current:",Imax,"Measured  current=", current)
                #raiseError("Measured current exceeds max requested, aborting run")
           
            for i in range(repeats):
            
                #A quick sleep between measurements
                time.sleep(1.5)
            
                #Make the oscilloscope trigger and save some data                 
                currVolt = str(abs(targetVoltage)).zfill(3)
                currRepeat = str(i).zfill(2);
                
                myOSC.singleMeasurement()
                time.sleep(0.25) #Need to allow the OSC to perform this action 
                
                fileName = save_folder + '\\Data\\' + str(currVolt) + 'V_R' + str(currRepeat)
                print("fileName = " + str(fileName))
                myOSC.saveWaveformXY(fileName)
                           
                ########## NOTE THAT THE INFINIIUM MUST BE ON DISPLAY FOR THIS TO WORK ##########
                fileName = save_folder + '\\Images\\' + str(currVolt) + 'V_R' + str(currRepeat)
                print("fileName = " + str(fileName))
                myOSC.saveScreenGrab(fileName) 
                    
                    
                
                    
                #print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

            comment = ""
     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    ps.controlSource('off')
    #save plots
    #print('Saving CV plots...')
    #plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    #plotC2.mainplt.savefig('{0}/C2V_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    #print('Closing {0}...'.format(save_path))
    #data.close()
    #plot.close()
    #plotC2.close()
    
    #for i in range(len(pltData)):
    #    pltData[i].close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status
    
def jmCollectHits(myOSC, save_folder, runTime):
    #So some assumptions for this test measurement:
    #That the oscilloscope is setup auto triggering and all your settings are as you want them
    #All we need to do is set to single trigger mode
    #Trigger
    #Record the data
    #Move onto next voltage (but for now we will just test the saving aspect
    
    status=0 #0=success, 1=fail
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    try:
    
        #One of the first tings we will do is to make the relevant directories 
        #(I don't think it overwrites anything, but we are only doing this once 
        #at the start anyway
        #We have to do each folder separately
        myOSC.mkdir(save_folder)
        myOSC.mkdir(save_folder + '\\Data\\')
        myOSC.mkdir(save_folder + '\\Images\\')

        #This will run on  continuous loop until you press Ctrl-C in the terminal to cancel it
        myOSC.singleMeasurement()
        
        #Set to a non zero value if you want to continue from a previous run
        count = 0;
        while(True):
        
            #Cheeck if single measurement has been made
        
            #time.sleep(0.25) #Need to allow the OSC to perform this action 
            
            if myOSC.triggered():
                count = count + 1
                countStr = str(count).zfill(6)

                print("Event_" + str(countStr) + "_Captured")
                
                fileName = save_folder + '\\Data\\Event_' + str(countStr)
                myOSC.saveWaveformXY(fileName)
                
                time.sleep(0.5) #Need to allow the OSC to perform this action 
                #time.sleep(1.0)
                
                ########## NOTE THAT THE INFINIIUM MUST BE ON DISPLAY FOR THIS TO WORK ##########
                #fileName = save_folder + '\\Images\\Event_' + str(countStr)
                #myOSC.saveScreenGrab(fileName) 
                        
                myOSC.singleMeasurement()  
                time.sleep(0.2)  
                #time.sleep(1.2)                
            #else:
                #No need to go crazy and probe ALL the time
                #time.sleep(0.01)
                    
                #print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

            comment = ""
     
    except Exception as e:
        print(e)
        status=1

    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status

def jmCollectHits_Fixed(myOSC, ps, Voltages, save_folder, runTime):
    #So some assumptions for this test measurement:
    #That the oscilloscope is setup auto triggering and all your settings are as you want them
    #All we need to do is set to single trigger mode
    #Trigger
    #Record the data
    #Move onto next voltage (but for now we will just test the saving aspect
    
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    status=0 #0=success, 1=fail
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    try:
    
    
        voltageCheck=float(ps.readVoltageAndCurrent()[0])
            #if fabs(float(Vstart)-float(voltageCheck))>float(voltageTolerance):
            #    print("Target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck)
            #    comment = "Initial voltage did not match that requested, aborting"
            #    raiseError("Initial voltage did not match that requested, aborting")
            #if fabs(Voltages[0]-voltageCheck)>voltageTolerance:
        if fabs(0-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",Voltages[0],"Measured starting voltage=", voltageCheck)
            comment = "Initial voltage did not match that requested, aborting"
            raiseError("Initial voltage did not match that requested, aborting")
    
        count = 0;
        for i in range(len(Voltages)):
            
            targetVoltage = Voltages[i]
            
            #One of the first tings we will do is to make the relevant directories 
            #(I don't think it overwrites anything, but we are only doing this once 
            #at the start anyway
            #We have to do each folder separately
            targetVoltageStr = str(targetVoltage).zfill(3)
            
            specific_folder = save_folder + "\\Vbias_" + targetVoltageStr + "V"
            
            myOSC.mkdir(save_folder)
            myOSC.mkdir(specific_folder)
            myOSC.mkdir(specific_folder + '\\Data\\')
            myOSC.mkdir(specific_folder + '\\Images\\')          

            print("index = " + str(i) + "  (" + str(i+1) + " / " + str(len(Voltages)) + ")")
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            RampUp(ps, targetVoltage)
            #ps.setVoltage(targetVoltage)
            print("Checking compliance")
            #if ps.hitCompliance(5):
                #comment = "PS has hit compliance at voltage:{} aborting run".format(targetVoltage)
                #raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))

            time.sleep(5)
            voltage, current = ps.readVoltageAndCurrent()
            
            #check voltage makes sense
            if fabs(float(targetVoltage)-float(voltage))>float(voltageTolerance):
                comment = "Measured voltage does not match that observed, aborting run"
                print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                raiseError("Measured voltage does not match that observed, aborting run")

            
            #This will run on  continuous loop until you press Ctrl-C in the terminal to cancel it
            myOSC.singleMeasurement() 
            
            
            timeAtStart = time.time()
            oldCount = count
            count = 0
            if i > 0:
                if Voltages[i] == Voltages[i-1]:
                    count = oldCount
            while(True):
            
                #Cheeck if single measurement has been made
            
                #time.sleep(0.25) #Need to allow the OSC to perform this action 
                
                if myOSC.triggered():
                    count = count + 1
                    countStr = str(count).zfill(6)

                    secondsLeft = runTime - fabs(time.time() - timeAtStart)
                    minutesLeft = round(secondsLeft / 60)

                    print("Vbias " + targetVoltageStr + "V: Event_" + str(countStr) + "_Captured   " + str(minutesLeft) + " minutes left")
                    
                    fileName = specific_folder + '\\Data\\Event_' + str(countStr)
                    myOSC.saveWaveformXY(fileName)
                    
                    time.sleep(0.5) #Need to allow the OSC to perform this action 
                    #time.sleep(1.0)
                    
                    ########## NOTE THAT THE INFINIIUM MUST BE ON DISPLAY FOR THIS TO WORK ##########
                    #fileName = save_folder + '\\Images\\Event_' + str(countStr)
                    #myOSC.saveScreenGrab(fileName) 
                            
                    #Now check how long we have been running for
                  
                    if secondsLeft < 0:
                        break;
                            
                    myOSC.singleMeasurement()  
                    time.sleep(0.2)  
                    #time.sleep(1.2)                
                #else:
                    #No need to go crazy and probe ALL the time
                    #time.sleep(0.01)
                        
                    #print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

                comment = ""
         
    except Exception as e:
        print(e)
        status=1

    RampDown(ps,rampDownStep,rampDownWait)
    ps.controlSource('off')
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status

def jmMeasureIV(ps,save_path,pltFormatFile,Voltages,Imax,InitCurrentRange,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time):
    # IV test using single power supply to apply voltage and measure current. 
    
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    currentCurrentRange = InitCurrentRange
    
    #Setdata file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time PS Voltage(V) PS Current(A)\n')
    print('{0} created successfully...'.format(save_path))


    #Alternate Saving Path
    pltData = open(pltFormatFile, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    pltData.write('PS Voltage(V) PS Current(A) #Date-Time\n')
    pltData.write('x,y\n')


    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = IVPlotWindow()
    plot.open()
    print('Opening time plot window...')
    #timeplot = TimePlot()
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    try:
        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        #if fabs(Vstart-voltageCheck)>voltageTolerance:
        #    print("Target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck)
        #    raiseError("Initial voltage did not match that requested, aborting")
        #    comment = "Initial voltage did not match that requested, aborting"
        if fabs(Voltages[0]-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",Voltages[0],"Measured starting voltage=", voltageCheck)
            comment = "Initial voltage did not match that requested, aborting"
            raiseError("Initial voltage did not match that requested, aborting")
                  
        oldCurrentRange = currentCurrentRange
        
        #print(Vstart,Vfinal,Vstep)
        print(min(Voltages),max(Voltages))
        #for targetVoltage in np.arange(Vstart,Vfinal+Vstep,Vstep):
        #for index in range(len(Voltages)):
        index = -1
        while index < len(Voltages) - 1:              
            index = index + 1
            print("")
            print("index = " + str(index) + "  (" + str(index+1) + " / " + str(len(Voltages)) + ")")
            targetVoltage = Voltages[index]
            
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            ps.setVoltage(targetVoltage)
            
            print("Waiting for " + str(rest_time) + "s before resuming")
            time.sleep(rest_time)
            
            
            print("Checking compliance")
            if ps.hitCompliance(nComplianceChecks):
                comment = "PS has hit compliance at voltage:{} aborting run".format(targetVoltage)
                raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))

            print("performing measurement")
            #perform measurement            
            
            voltage, current = ps.readVoltageAndCurrent()
            date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
            #check voltage makes sense                     
            
            print("Checking Voltage Tolerance")
            if fabs(targetVoltage-float(voltage))>voltageTolerance:
                print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                comment = "Measured voltage does not match that observed, aborting run"
                raiseError("Measured voltage does not match that observed, aborting run")           

            
            #The if statement below handles the current being too high. (I.e. hitting compliance. So that already works)
            #What we need to implement here is another check. We need to make sure that if it hits compliance, we have the
            #Current range set to the maximum (it may just be exceeding the current range)
            #This maximum is simply the order of magnitude of the compliance/IMax.
            #So what we do is check whether we can increase the current range and then rerun this loop (and voltage)
                        
            #check current makes sense
            print("Checking Current Level")
            if float(current)>Imax:
                print("Maximum current:",Imax,"Measured current=", current)
                
                maxCurrentRange = math.floor(math.log10(Imax))
                if (currentCurrentRange >= maxCurrentRange):                    
                    #Hit the max so go and raise an error
                    comment = "Measured current exceeds max requested, aborting run"
                    raiseError("Measured current exceeds max requested, aborting run")                    
                else:
                    #If we haven't hit the max, go and increase the range by 1
                    print("Maximum current exceeded, increasing the current range from " + str(currentCurrentRange) + " to " + str(currentCurrentRange + 1))                    
                    print("")                    
                    currentCurrentRange = currentCurrentRange + 1
                    ps.setCurrentRange(pow(10, currentCurrentRange))
                    index = index - 1; #To make sure we repeat this voltage
                    comment = "Maximum current exceeded, increasing the current range from " + str(oldCurrentRange) + " to " + str(currentCurrentRange)
                
            else:
                #Need to be within an else to make sure we don't record this measurement
                
                #write IV to file
                measurement = [date_time, voltage, current]
                measurement = [(str)(x) for x in measurement]
                                
                #Can update this now that we have made it through
                oldCurrentRange = currentCurrentRange
                
                data.write(' '.join(measurement) + '\n')
                pltData.write(str(float(voltage)) + ',' + str(float(current)) + ",   " + date_time + ",   " + comment + '\n')
                #pltData.write(voltage + ',' + current + ",   " + date_time + ",   " + comment + '\n')
    
                #plot
                long_measurement = [date_time, voltage, current, temperature, humidity]
                plot.update(long_measurement)
                #timeplot.update(long_measurement)
                print('At {0}: V = {1} V, I = {2} A, T = {3} C, RH = {4}%.'.format(*long_measurement))
                
                comment = ""
               
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        status=1
        errorThrown = True
        
    if not errorThrown:
        comment = "Measurements ended naturally"
    pltData.write('END\n' + comment + '\n')    
    
    #ramp down power supply and turn off output
    print('Ramping Down...')
    RampDown(ps,rampDownStep,rampDownWait)
    print('Ramping Down Finished')
    ps.controlSource('off')
    #save plots
    print('Saving IV plots...')
    plot.mainplt.savefig('{0}/Results/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    #timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    pltData.close()
    plot.close()
    #timeplot.close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status
    
    
def jmSpiralSearch(XlC, myOSC, linked_folder, save_folder):
    #So some assumptions for this test measurement:
    #That the oscilloscope is setup auto triggering and all your settings are as you want them
    #All we need to do is set to single trigger mode
    #Trigger
    #Record the data
    #Move onto next voltage (but for now we will just test the saving aspect
    
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    status=0 #0=success, 1=fail
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    print('')
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('Beginning Coarse Spiral Search')    
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('')
    
    #Object of this phase of the alignment.
    #We just want to find a signal somewhere. Doesn't have to be strong, just has to be something
    #We need to make sure that we cover every possible position (hence the spiral) but we need to make sure
    #we don't miss anything
    
    #Size of the pad is 1mm diameter. Assume that the laser is a point source (it is not, but this assumption
    #actually helps)
    #So a max distance of 1000um is needed.
    #Let's choose 500um for simplicitiy.
    
    #Spirals are defined as r = a*x, where r is the distance from the origin, a is a parameter and x is the angle (in any units)
    #the x & y coords are simply y = r.sin(x) = ax.sin(x) and y = ax.cos(x)
    
    #The distance between two positions is just sqrt((y2-y1)^2 + (x2-x1)^2) = d. This distance needs to be the 500um minimum distance
    #But also, so does the difference between two revolutions
    #So r' = a*(x + 360) #Assuming degrees
    #Actually, the difference r' - r is ax + 360a - ax = 360a
    #So depending on coord system (which all works out in the end), you need 360a = 500um
    
    #We could perform a simple numerical search function to find the value of x which satisfies d = 500um (to a 1um precision)
    #This initial iteration will chosea very small x step size and keep going still d > 500um. Then it will move there and record
    #Incase we miss the target (which is possible). We will set an angular limit of b rotations.
    #Given we have just defined the distance between revolutions as 500um. We can choose a search radius to define b
    
    #So the units. x is in degrees. r is in um
    #That makes a = 500um / 360degrees
    #Now we just have to trial angles until we reach d > 500um
    
    #minimumTravel = 500 #um  
    minimumTravel = 500 #um   #was 500um NN HERE
    #searchRadius = 15 * 1000 #um
    searchRadius = 15 * 1000 #um
    
    a = minimumTravel / 360   
    b = searchRadius / minimumTravel
    maxAngle = b * 360
    angleStep = 0.1 #degrees        

    try:
        #We are now ready to begin moving the sensor around by increase x.
        
        x = 0 #Might as well start here as it can't be further than 500um until this point by very definition
        #x = 270 #For Debug
        
        #Set to a ridiculous value so that x=0 will be selected as the first point
        lastX = 100000
        lastY = 100000
        
        newX = 0
        newY = 0
        r = 0
        #Then begin the loop of increasing angle slowly
        while True:
                                 
            #So find that angle
            while True:                               
                #Calculate distance to last position
                r = a*x
                newX = r * np.sin(x/180 * np.pi)
                newY = r * np.cos(x/180 * np.pi)
                
                d = np.sqrt( ((newX - lastX)*(newX - lastX)) + ((newY - lastY)*(newY - lastY)) )
                
                if d >= minimumTravel:
                    break;
                    
                #This is added because by definition the spiral with jump from home to this. 
                #The problem is that means it cuts out the initial part of a spiral
                #So keeping the minimumTravel the same, we are just going to do a small circle with
                #a radius of half this value. Should be ideal.
                if x < 360:
                    x = x + 30
                    
                    r = (minimumTravel / 2)
                    newX = r * np.sin(x/180 * np.pi)
                    newY = r * np.cos(x/180 * np.pi)
                    
                    break
                
                #Moved to the end so that we actually start at (0,0)                
                x = x + angleStep
                #x = x + 360 #For Debug
        
            lastX = newX
            lastY = newY
            
            periodicAngle = x - (int(x / 360) * 360)
            
            #Now we move to the new position and measure
            print("")
            print("New Position:")#
            print("r = {0}; x = {2} ({1})".format(r, periodicAngle, x))
            print("newX = {0}; newY = {1}".format(newX, newY))
                    
            #Movement
            XlC.move_to_microns(XlC.deviceID_1, newX)            
            XlC.move_to_microns(XlC.deviceID_2, newY)            
            #We should be able to move both axes at once
            XlC.wait_for_stop(XlC.deviceID_1, 100)            
            XlC.wait_for_stop(XlC.deviceID_2, 100)
            
            
            overVoltageThreshold = 40e-3 #V
            validSignalThreshold = -50e-3 #V #-75e-3
            #^ This was 50mV. I've decided to up it for the PiN so that we do not accidentally find the guard ring (or whatever we are picking up at the edges)
            #Should still be okay provided a high enough laser power and bias voltage is used
            
            minVolt = 0
            
            #Run a loop until we get a valid waveform
            while True:
                #Measurement            
                myOSC.singleMeasurement()
                time.sleep(0.2) #Need to allow the OSC to perform this action                            
                
                fileName = linked_folder
                print("fileName = " + str(fileName))
                myOSC.saveWaveformXY(fileName)                       
                
                time.sleep(1) #Need to allow the OSC to perform this action                            
                
                
                #Analysis

                startIndex = 24
                success = False                
                while not success:
                    success, data = Read_XYFormat(save_folder, ".csv", False, startIndex)
                Time = data[:,0]
                trigVolt = data[:,1]
                Volt = data[:,2]
                bmVolt = data[:,3]
            
                #All we really need to check for is (over voltage) and a certain threshold of negative voltage           
                minVolt = min(Volt)
            
                #Check that the signal is valid. If the voltage goes too high (positive)
                #Then we need to retake the waveform
                if max(Volt) < overVoltageThreshold:                    
                    break;
                print("Overvoltage Found. Retaking Waveform")
            
            #Check whether the position we have found is a valid enough signal.
            #If so, zero this position and and end this part of the search
            if minVolt < validSignalThreshold:
                print("")
                print("")
                print("LASER ALIGNMENT SUCCESSFUL")
                print("New Home Position Set At:")#
                print("r = {0}; x = {2} ({1})".format(a*x, periodicAngle, x))
                print("newX = {0}; newY = {1}".format(newX, newY))
                XlC.set_zero_pos(XlC.deviceID_1)
                XlC.set_zero_pos(XlC.deviceID_2)
                break;
            
            
            #Check for overangle
            if x > maxAngle:
                print("")
                print("")
                print("LASER ALIGNMENT FAILED")
                print("Maximum search radius reached")
                XlC.return_home(XlC.deviceID_1)
                XlC.return_home(XlC.deviceID_2)
                XlC.wait_for_stop(XlC.deviceID_1, 100)            
                XlC.wait_for_stop(XlC.deviceID_2, 100)
                status=1
                break;
                
            print("Sufficient signal not found ({0} vs {1}). Moving to next position".format(minVolt, validSignalThreshold))         
    except KeyboardInterrupt:
        print ("Keyboard Interruption. Returning home")
        XlC.return_home(XlC.deviceID_1)
        XlC.return_home(XlC.deviceID_2)
        XlC.wait_for_stop(XlC.deviceID_1, 100)            
        XlC.wait_for_stop(XlC.deviceID_2, 100)
        status=1
    except Exception as e:
        print(e)
        status=1           
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status
    
def jmFineSearch2Dx2(XlC, myOSC, linked_folder, save_folder, scan_folder):
    
    status = 0 #0=success, 1=fail
    
    print('')
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('Beginning 2Dx2 Fine Lateral Search')
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print('')
   
    #print('Beginning 2Dx2 Fine Lateral Search')
    
    print("")
    print('Scanning X Direction #1')
    scan_filename = "Scan1_X_Direction"
    stat = jmFineSearch1D(XlC, myOSC, linked_folder, save_folder, scan_folder, scan_filename, XlC.deviceID_1)
    if stat == 1: status = 1
    
    print("")
    print('Scanning Y Direction #1')
    scan_filename = "Scan1_Y_Direction"
    stat = jmFineSearch1D(XlC, myOSC, linked_folder, save_folder, scan_folder, scan_filename, XlC.deviceID_2)
    if stat == 1: status = 1
    
    print("")
    print('Scanning X Direction #2')
    scan_filename = "Scan2_X_Direction"
    stat = jmFineSearch1D(XlC, myOSC, linked_folder, save_folder, scan_folder, scan_filename, XlC.deviceID_1)
    if stat == 1: status = 1
    
    print("")
    print('Scanning Y Direction #2')
    scan_filename = "Scan2_Y_Direction"
    stat = jmFineSearch1D(XlC, myOSC, linked_folder, save_folder, scan_folder, scan_filename, XlC.deviceID_2)
    if stat == 1: status = 1


    return status
    
def jmFineSearch1D(XlC, myOSC, linked_folder, save_folder, scan_folder, scan_filename, device_ID):
    #So some assumptions for this test measurement:
    #We are assuming we have already hit the target in some way
    
    #This function is also a simple scan in one axis/direction.
    #We can call this multiple times if we so please
    
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0 
    
    status=0 #0=success, 1=fail
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    #print('')
    #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #print('Beginning Fine Lateral Search')
    #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #print('')

    try:
        #scanDistance = 2000 #um  +- from home position
        scanDistance = 500 #um  +- from home position #NN HERE
        #scanStep = 25
        scanStep = 20 #NN HERE
        
        positions = []
        heights = []
        integrals = []
        
        overVoltageThreshold = 100e-3 #V marcus changed this to 100mV from 40mV
        validSignalThreshold = -40e-3 #V
        
        #Now scan through each position. 
        #Take a waveform. 
        #Calcualte the integral
        #Correct for the beam monitor (optional)
        #Append and move on
        
        print("")        
        print("Moving backwards")
        print("")
        loopEnd = -scanDistance
        stopCheck = False
        #for newPos in range(0, loopEnd, -scanStep):
        newPos = scanStep
        while newPos > loopEnd:
            newPos = newPos - scanStep
            #print(newPos, loopEnd)
        
            XlC.move_to_microns(device_ID, newPos)                       
            XlC.wait_for_stop(device_ID, 100)

            Time = []
            Volt = []
            while True:
                #Measurement            
                myOSC.singleMeasurement()
                time.sleep(0.2) #Need to allow the OSC to perform this action                            
                
                fileName = linked_folder
                print("fileName = " + str(fileName))
                myOSC.saveWaveformXY(fileName)                       
                
                time.sleep(1) #Need to allow the OSC to perform this action                            
                
                
                #Analysis
                startIndex = 24
                success = False                
                while not success:
                    success, data = Read_XYFormat(save_folder, ".csv", False, startIndex)
                Time = data[:,0]
                trigVolt = data[:,1]
                Volt = data[:,2]
                bmVolt = data[:,3]

                #Check that the signal is valid. If the voltage goes too high (positive)
                #Then we need to retake the waveform
                if max(Volt) < overVoltageThreshold:          
                    break
                print("Overvoltage Found. Retaking Waveform")
        

            if min(Volt) > validSignalThreshold:                
                if not stopCheck:
                    stopCheck = True
                    print("Max Voltage too small. Moving on in 5 more steps")
                    loopEnd = newPos - (5*scanStep)
         
            #If we made it this far, perform the analysis
            #Calculate integral and move on
                    
            #Firstly find the minimum
            minVolt = min(Volt)
            timeAtMin = 0
            for i in range(len(Time)):
                if Volt[i] == minVolt:
                    timeAtMin = Time[i]
                    break
                    
            #Then define an area around it to integrate (sufficiently large)
            timeBefore = 5e-9 #20e-9
            timeAfter = 10e-9 #20e-9
            #We could be more refined, but I think it's fine to be coarse
            timeStep = Time[1] - Time[0]
            startTime = timeAtMin - timeBefore
            endTime = timeAtMin + timeAfter
            integral = 0
            for i in range(len(Time)):
                if Time[i] > startTime:
                    if Time[i] < endTime:
                        integral = integral + (timeStep * Volt[i])
         
            positions.append(newPos)
            integrals.append(-integral)
            heights.append(-min(Volt))
         
        print("")        
        print("Moving forwards")
        print("")
        #Repeat for the other direction 
        loopEnd = scanDistance
        stopCheck = False
        #for newPos in range(scanStep, loopEnd, scanStep):
        newPos = 0
        while newPos < loopEnd:
            newPos = newPos + scanStep
            XlC.move_to_microns(device_ID, newPos)                       
            XlC.wait_for_stop(device_ID, 100)

            Time = []
            Volt = []
            while True:
                #Measurement            
                myOSC.singleMeasurement()
                time.sleep(0.2) #Need to allow the OSC to perform this action                            
                
                fileName = linked_folder
                print("fileName = " + str(fileName))
                myOSC.saveWaveformXY(fileName)                       
                
                time.sleep(1) #Need to allow the OSC to perform this action                            
                
                
                #Analysis
                startIndex = 24
                success = False
                while not success:
                    success, data = Read_XYFormat(save_folder, ".csv", False, startIndex)
                Time = data[:,0]
                trigVolt = data[:,1]
                Volt = data[:,2]
                bmVolt = data[:,3]

                #Check that the signal is valid. If the voltage goes too high (positive)
                #Then we need to retake the waveform
                if max(Volt) < overVoltageThreshold:          
                    break
                print("Overvoltage Found. Retaking Waveform")
        
            if min(Volt) > validSignalThreshold:                
                if not stopCheck:
                    stopCheck = True
                    print("Max Voltage too small. Moving on in 5 more steps")
                    loopEnd = newPos + (5*scanStep)
                
                
            #If we made it this far, perform the analysis
            #Calculate integral and move on
                    
            #Firstly find the minimum
            minVolt = min(Volt)
            timeAtMin = 0
            for i in range(len(Time)):
                if Volt[i] == minVolt:
                    timeAtMin = Time[i]
                    break
                    
            #Then define an area around it to integrate (sufficiently large)
            timeBefore = 20e-9
            timeAfter = 20e-9
            #We could be more refined, but I think it's fine to be coarse
            timeStep = Time[1] - Time[0]
            startTime = timeAtMin - timeBefore
            endTime = timeAtMin + timeAfter
            integral = 0
            for i in range(len(Time)):
                if Time[i] > startTime:
                    if Time[i] < endTime:
                        integral = integral + (timeStep * Volt[i])
         
            positions.append(newPos)
            integrals.append(-integral) 
            heights.append(-min(Volt))            
                
                
        #Now rearrange the data into order and do a final analysis and homing
        #Plus save the image
        orderedIntegrals = d2SortX(positions, integrals)
        orderedHeights = d2SortX(positions, heights)
        
        #Save as a .plt and a plot
        Write_StandardPltFormat(scan_folder + "\\Integral_Data", scan_filename + "_integral_pltData", "x,y", orderedIntegrals)
        Write_StandardPltFormat(scan_folder + "\\Height_Data", scan_filename + "_height_pltData", "x,y", orderedHeights)
        
        #If we choose to. Either analyse the data and move to a new home, or return to the original home
        maxHeight = max(orderedHeights[1])
        factor = 0.75
        threshold = factor * maxHeight
        
        firstCrossing = 0
        secondCrossing = 0
        
        for i in range(1, len(orderedHeights[1])-1, 1):
            if orderedHeights[1][i] > threshold:   
                #We need to check that there is actually a solution to the problem, otherwise report an error
                if orderedHeights[1][i-1] < threshold:
                    firstCrossing = linearInterpolation_2pT(orderedHeights[0][i-1], orderedHeights[0][i], orderedHeights[1][i-1], orderedHeights[1][i], threshold)
                else:
                    firstCrossing = orderedHeights[0][i]
                    print("No valid paramters for interpolation (device not likely found by spiral search")
                #print("")
                #print("threshold crossed at: " + str(orderedHeights[1][i]))
                #print("i = " + str(i))
                #print("interpolating between {0} and {1}".format(orderedHeights[0][i-1], orderedHeights[0][i]))
                #print("with heights: {0} and {1}".format(orderedHeights[1][i-1], orderedHeights[1][i]))
                #print("firstCrossing = " + str(firstCrossing))
                #print("")
                break

        for i in range(len(orderedHeights[1])-2, 0, -1):
            if orderedHeights[1][i] > threshold:
                if orderedHeights[1][i+1] < threshold:
                    secondCrossing = linearInterpolation_2pT(orderedHeights[0][i+1], orderedHeights[0][i], orderedHeights[1][i+1], orderedHeights[1][i], threshold)        
                else:
                    secondCrossing = orderedHeights[0][i]
                    print("No valid paramters for interpolation (device not likely found by spiral search")
                #print("")
                #print("threshold crossed at: " + str(orderedHeights[1][i]))
                #print("i = " + str(i))
                #print("interpolating between {0} and {1}".format(orderedHeights[0][i-1], orderedHeights[0][i]))
                #print("with heights: {0} and {1}".format(orderedHeights[1][i-1], orderedHeights[1][i]))
                #print("secondCrossing = " + str(secondCrossing))
                #print("")
                break
 
        middle = round((secondCrossing + firstCrossing) / 2)
 
        print("")
        print("!!!!!")
        print("Scan Summary")
        print("factor = " + str(factor))
        print("maxHeight = " + str(maxHeight))
        print("threshold = " + str(threshold))
        print("firstCrossing = " + str(firstCrossing))
        print("secondCrossing = " + str(secondCrossing))
        print("middle = " + str(middle))
        print("!!!!!")
        print("")
         
        XlC.move_to_microns(device_ID, middle)                       
        XlC.wait_for_stop(device_ID, 100)
        XlC.set_zero_pos(device_ID)   
 
        plotter.cla()
        plotter.plot(orderedHeights[0], orderedHeights[1])            
        plotter.axhline(y=threshold, color='k', linestyle='--')
        plotter.axvline(x=firstCrossing, color='k', linestyle='--')
        plotter.axvline(x=secondCrossing, color='k', linestyle='--')        
        plotter.axvline(x=middle, color='k', linestyle='-.')        
        plotter.savefig(scan_folder + "\\Height_Plots\\" + scan_filename + "_height_plot")

        plotter.cla()
        plotter.plot(orderedIntegrals[0], orderedIntegrals[1])        
        plotter.savefig(scan_folder + "\\Integral_Plots\\" + scan_filename + "_integral_plot")       
 
        #XlC.return_home(device_ID)
        #XlC.wait_for_stop(device_ID, 100)
        #plotter.plot(orderedIntegrals[0], orderedIntegrals[1])        
        #plotter.savefig(scan_folder + "\\" + scan_filename + "_integral_plot")
        #plotter.cla()
        #plotter.plot(orderedHeights[0], orderedHeights[1])            
        #plotter.savefig(scan_folder + "\\" + scan_filename + "_height_plot")
        

        
    except Exception as e:
        print(type(e))
        print(e.args)
        print(e)
        print("Error on line: " + str(sys.exc_info()[-1].tb_lineno))
        status=1
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status
    
    
def jmBeamMonitoring(myOSC, linked_folder, save_folder, folder_name):
    #So some assumptions for this test measurement:
    #We are assuming we have already hit the target in some way
    
    #This function is also a simple scan in one axis/direction.
    #We can call this multiple times if we so please
    
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    status=0 #0=success, 1=fail
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    #print('')
    #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #print('Beginning Fine Lateral Search')
    #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #print('')

    

    try:
        #We are basically running a loop, just like in the timing setup
        #But we are taking a measuremnt every so often (say 5 or 10 seconds) 
        #rather than every trigger

        specific_folder = linked_folder + "\\" + folder_name
        
        myOSC.mkdir(specific_folder)
        myOSC.mkdir(specific_folder + '\\Raw_Data\\')        

        time.sleep(1) 

        runTime = 20 * 60
        waitTime = 5
        
        timeAtStart = time.time()
        times = []
        sigIntegrals = []
        bmIntegrals = []
        sigHeights = []
        bmHeights = []
        while(True):
        
            #Cheeck if single measurement has been made
        
            #time.sleep(0.25) #Need to allow the OSC to perform this action 
            
            myOSC.singleMeasurement()  
            time.sleep(0.25)  
            
            timeSinceStart = int(round(fabs(time.time() - timeAtStart)))
            
            timeStr = str(timeSinceStart).zfill(6)

            secondmnysLeft = runTime - timeSinceStart
            secondsLeft = runTime - timeSinceStart
            minutesLeft = round(secondsLeft / 60)

            print("SecondsSinceStart_" + str(timeStr) + " Captured   " + str(minutesLeft) + " minutes left")
            
            fileName = linked_folder + "\\" + folder_name +  '\\Raw_Data\\SecondsSinceStart_' + str(timeStr)
            fileName_local = save_folder + "\\" + folder_name + '\\Raw_Data\\SecondsSinceStart_' + str(timeStr)
            #print("Saving to: " + str(fileName))
            myOSC.saveWaveformXY(fileName)
            
            time.sleep(1.0) #Need to allow the OSC to perform this action 
            #time.sleep(1.0)
            
            ########## NOTE THAT THE INFINIIUM MUST BE ON DISPLAY FOR THIS TO WORK ##########
            #fileName = save_folder + '\\Images\\Event_' + str(countStr)
            #myOSC.saveScreenGrab(fileName) 
                    
            #Perform some analysis here
            startIndex = 24
            success = False            
            while not success:
                success, data = Read_XYFormat(fileName_local, ".csv", False, startIndex)
            Time = data[:,0]
            trigVolt = data[:,1]
            Volt = data[:,2]
            bmVolt = data[:,3]
                    
            #Firstly find the minimum
            minVolt = min(Volt)
            timeAtMin = 0
            for i in range(len(Time)):
                if Volt[i] == minVolt:
                    timeAtMin = Time[i]
                    break
                    
            #Then define an area around it to integrate (sufficiently large)
            timeBefore = 20e-9
            timeAfter = 20e-9
            #We could be more refined, but I think it's fine to be coarse
            timeStep = Time[1] - Time[0]
            startTime = timeAtMin - timeBefore
            endTime = timeAtMin + timeAfter
            sigIntegral = 0
            for i in range(len(Time)):
                if Time[i] > startTime:
                    if Time[i] < endTime:
                        sigIntegral = sigIntegral + (timeStep * Volt[i])
         
         
         
            #Firstly find the minimum
            minVolt = max(bmVolt)
            timeAtMin = 0
            for i in range(len(Time)):
                if bmVolt[i] == minVolt:
                    timeAtMin = Time[i]
                    break
                    
            #Then define an area around it to integrate (sufficiently large)
            timeBefore = 30e-9
            timeAfter = 230e-9
            #We could be more refined, but I think it's fine to be coarse
            timeStep = Time[1] - Time[0]
            startTime = timeAtMin - timeBefore
            endTime = timeAtMin + timeAfter
            bmIntegral = 0
            for i in range(len(Time)):
                if Time[i] > startTime:
                    if Time[i] < endTime:
                        bmIntegral = bmIntegral + (timeStep * bmVolt[i])
         
         
         
            times.append(timeSinceStart)
            bmIntegrals.append(bmIntegral) 
            bmHeights.append(max(bmVolt))   
            sigIntegrals.append(-sigIntegral) 
            sigHeights.append(-min(Volt))              
                    
            #Now check how long we have been running for                                            
            if secondsLeft < 0:
                break;
                    
            time.sleep(waitTime)
        
        
        Write_StandardPltFormat(save_folder + "\\" + folder_name , "bm_Heights_pltData", "x,y", [times, bmHeights])
        Write_StandardPltFormat(save_folder + "\\" + folder_name , "bm_Integrals_pltData", "x,y", [times, bmIntegrals])
        Write_StandardPltFormat(save_folder + "\\" + folder_name , "sig_Heights_pltData", "x,y", [times, sigHeights])
        Write_StandardPltFormat(save_folder + "\\" + folder_name , "sig_Integrals_pltData", "x,y", [times, sigIntegrals])
        
        plotter.cla()
        plotter.plot(times, bmHeights)        
        plotter.savefig(save_folder + "\\" + folder_name + "\\bm_Heights_plot")    
        
        plotter.cla()
        plotter.plot(times, bmIntegrals)        
        plotter.savefig(save_folder + "\\" + folder_name + "\\bm_Integrals_plot")    
        
        plotter.cla()
        plotter.plot(times, sigHeights)        
        plotter.savefig(save_folder + "\\" + folder_name + "\\sig_Heights_plot")    
        
        plotter.cla()
        plotter.plot(times, sigIntegrals)        
        plotter.savefig(save_folder + "\\" + folder_name + "\\sig_Integrals_plot")    
        
    except Exception as e:
        print(e)
        status=1
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status


def jmTimingEfficiency(myOSC, linked_folder, save_folder, fileName, runTime):
#So some assumptions for this test measurement:
    #That the oscilloscope is setup auto triggering and all your settings are as you want them
    #All we need to do is set to single trigger mode
    #Trigger
    #Record the data
    #Move onto next voltage (but for now we will just test the saving aspect
    
    voltageTolerance=0.01 #V
    rampDownStep=5.0 #V
    rampDownWait=0.25 #s #Used to be 0.5, but the LabView used 0.1. Which is 5 times faster...
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    status=0 #0=success, 1=fail
    
    print("Setup complete- beginning test")
    comment = ""

    errorThrown = False

    try:
    
        fileName_local = linked_folder + "\\" + fileName
        fileName_summary = linked_folder + "\\Summary.txt"
        
        #This will run on  continuous loop until you press Ctrl-C in the terminal to cancel it
        myOSC.singleMeasurement() 
                
        timeAtStart = time.time()
        count = 0
        numOfCoinc = 0
        while(True):
        
            #Cheeck if single measurement has been made
        
            #time.sleep(0.25) #Need to allow the OSC to perform this action 
            
            if myOSC.triggered():
                count = count + 1
                countStr = str(count).zfill(6)

                secondsLeft = runTime - fabs(time.time() - timeAtStart)
                minutesLeft = round(secondsLeft / 60)
                
                #fileName = specific_folder + '\\Data\\Event_' + str(countStr)
                myOSC.saveWaveformXY(fileName_local)
                
                time.sleep(0.5) #Need to allow the OSC to perform this action 
                #time.sleep(1.0)
                
                message = "Triggered!   " + str(round(secondsLeft)) + " s remaining"                
                
                ########## NOTE THAT THE INFINIIUM MUST BE ON DISPLAY FOR THIS TO WORK ##########
                #fileName = save_folder + '\\Images\\Event_' + str(countStr)
                #myOSC.saveScreenGrab(fileName) 
                        
                #Now check how long we have been running for
              
                if secondsLeft < 0:
                    break;
                        
                myOSC.singleMeasurement()  
                time.sleep(0.2)  
                
                #While it sits and triggers, run the analysis *Should* simulate the real thing a little bit better
                startIndex = 24
                success = False            
                while not success:
                    success, data = Read_XYFormat(fileName_local, ".csv", False, startIndex)
                Time = data[:,0]
                botDUT = data[:,1]
                topDUT = data[:,2]
                
                threshold = 50e-3 #V (50mV)
                
                if max(botDUT) > threshold:
                    if max(topDUT) > threshold:
                        numOfCoinc = numOfCoinc + 1
                        message = message + "   <- Coincidence Found!!!"
                
                print(message)
                #time.sleep(1.2)                
            #else:
                #No need to go crazy and probe ALL the time
                #time.sleep(0.01)
                    
                #print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

            comment = ""
     
        #Final calculations into a text file once this is done
        timeElapsed = fabs(time.time() - timeAtStart)
        efficiency = numOfCoinc / count * 100 #%
        countRate = numOfCoinc / timeElapsed
        triggerRate = count / timeElapsed
        
        #2000 counts prediction
        counts2kPrediction = -1
        if countRate > 0:        
            counts2kPrediction = 2000 / countRate
        
        txt = ""
        txt += "Timing Efficiency Summary\n\n\n"
        
        txt += "Time Elapsed: "
        txt += str(timeElapsed)
        txt += " s\n"
        txt += "Number of Triggers: "
        txt += str(count)
        txt += "\n"        
        txt += "Number of Counts (Coincidence Events): "
        txt += str(numOfCoinc)
        txt += "\n\n"
        
        txt += "Efficiency: "
        txt += str(efficiency)
        txt += " %\n"        
        txt += "Trigger Rate: "
        txt += str(triggerRate)
        txt += " per second\n"        
        txt += str(triggerRate*60)
        txt += " per min\n"      
        txt += "Count Rate: "
        txt += str(countRate)
        txt += " per second\n"
        txt += str(countRate*60)
        txt += " per min\n\n"
        txt += "Time to Achieve 2k counts:\n"
        if countRate > 0:
            txt += str(counts2kPrediction)
            txt += " s\n"
            txt += str(counts2kPrediction/60)
            txt += " min\n"
            txt += str(counts2kPrediction/60/60)
            txt += " hrs\n"
        else:
            txt += "No coincidence events found, so prediction cannot be made"
        txt += "\n"
     
        with open(fileName_summary, 'w') as f:
            f.write(txt)
     
    except Exception as e:
        print(type(e))
        print(e.args)
        print(e)
        print("Error on line: " + str(sys.exc_info()[-1].tb_lineno))
        status=1


    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status