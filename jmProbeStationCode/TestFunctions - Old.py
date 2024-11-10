#!/usr/bin/python
# MeasurementFunctions.py -- contains classes for running IV and CV tests
# Updated: 05/03/2021
# Contributing: Matt Basso (University of Toronto), Tim Knight (University of Toronto), Will George (University of Birmingham)

import sys, os, time
from Plots import IVTimePlot as TimePlot
from Plots import TwoIVPlotWindow as MD8TimePlot
from Plots import IVPlotWindow
from Plots import CVPlotWindow
from math import fabs
import numpy as np
import math

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


def measureIV(ps,save_path,Vstep,Vstart,Vfinal,Imax,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time):
    # IV test using single power supply to apply voltage and measure current. 
    
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=1.0 #V
    rampDownWait=0.5 #s
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    
    #Setdata file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time PS Voltage(V) PS Current(A)\n')
    print('{0} created successfully...'.format(save_path))

    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = IVPlotWindow()
    plot.open()
    print('Opening time plot window...')
    timeplot = TimePlot()
    
    print("Setup complete- beginning test")

    try:
        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        if fabs(Vstart-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck)
            raiseError("Initial voltage did not match that requested, aborting")
                  
        print(Vstart,Vfinal,Vstep)
        for targetVoltage in np.arange(Vstart,Vfinal+Vstep,Vstep):
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            ps.setVoltage(targetVoltage)
            
            print("Checking compliance")
            if ps.hitCompliance(5):
                raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))
            
            time.sleep(rest_time)

            print("performing measurement")
            #perform measurement
            
            
            voltage, current = ps.readVoltageAndCurrent()
            date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
            #check voltage makes sense
            
            if False:
                print("targetVoltage = " + str(targetVoltage) + " : " + str(type(targetVoltage)))
                print("voltage = " + str(voltage) + " : " + str(type(voltage)))
                print("voltageTolerance = " + str(voltageTolerance) + " : " + str(type(voltageTolerance)))
                
                dif = targetVoltage-float(voltage)
                print("dif)> = " + str(dif))
                print("fabs(dif) = " + str(fabs(dif)))           
            
            if fabs(targetVoltage-float(voltage))>voltageTolerance:
                print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                raiseError("Measured voltage does not match that observed, aborting run")           
            
            #check current makes sense
            if float(current)>Imax:
                print("Maximum current:",Imax,"Measured  current=", current)
                raiseError("Measured current exceeds max requested, aborting run")
                
            #write IV to file
            measurement = [date_time, voltage, current]
            measurement = [(str)(x) for x in measurement]
            data.write(' '.join(measurement) + '\n')

            #plot
            long_measurement = [date_time, voltage, current, temperature, humidity]
            plot.update(long_measurement)
            timeplot.update(long_measurement)
            print('At {0}: V = {1} V, I = {2} A, T = {3} C, RH = {4}%.'.format(*long_measurement))
     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    ps.controlSource('off')
    #save plots
    print('Saving IV plots...')
    plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    timeplot.close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status


def measureInterstripIV(ps,am,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time):
    
    # IV test using two power supplies: ps is ramped to a fixed voltage for the test and ramped down after again, am performs IV sweep and ramps down after. 
    
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=1.0 #V
    rampDownWait=0.5 #s
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    
    #Setdata file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time AM Voltage(V) AM Current(A)\n')
    print('{0} created successfully...'.format(save_path))

    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = IVPlotWindow()
    plot.open()
    print('Opening time plot window...')
    timeplot = TimePlot()

    print("Setup complete- beginning test")

    try:
    
        #ramp HV Bias
        successfulRamp=RampVoltage(ps,ps_Vinitial,ps_Vfinal,ps_Vstep)
        if successfulRamp==False:
            raiseError("Failed to reach target bias voltage")
            
        #ramp LV to starting point
        successfulRamp=RampVoltage(am,0.0,am_Vinitial,am_Vstep)
        if successfulRamp==False:
            raiseError("Failed to reach starting low voltage")
    

        print("Waiting for",first_point_rest_time,"s before starting measurements")
        time.sleep(first_point_rest_time)  

        #ramp LV and do measurement
        voltageCheck=float(am.readVoltageAndCurrent()[0])
        if fabs(am_Vinitial-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",am_Vinitial,"Measured starting voltage=", voltageCheck)
            raiseError("Initial voltage did not match that requested, aborting")
                  
        print(am_Vinitial,am_Vfinal,am_Vstep)
        for targetVoltage in np.arange(am_Vinitial,am_Vfinal+am_Vstep,am_Vstep):
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            am.setVoltage(targetVoltage)
            print("Checking compliance")
            if am.hitCompliance(5):
                raiseError("am has hit compliance at voltage:{} aborting run".format(targetVoltage))

            time.sleep(rest_time)
            
            print("performing measurement")
            #perform measurement
            voltage, current = am.readVoltageAndCurrent()
            date_time = time.strftime('%Y/%m/%d-%H:%M:%S')

            #check voltage makes sense
            if fabs(targetVoltage-voltage)>voltageTolerance:
                print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                raiseError("Measured voltage does not match that observed, aborting run")
            

            #write IV to file
            measurement = [date_time, voltage, current]
            measurement = [(str)(x) for x in measurement]
            data.write(' '.join(measurement) + '\n')

            #plot
            long_measurement = [date_time, voltage, current, temperature, humidity]
            plot.update(long_measurement)
            timeplot.update(long_measurement)
            print('At {0}: V = {1} V, I = {2} A, T = {3} C, RH = {4}%.'.format(*long_measurement))

     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    RampDown(am,rampDownStep,rampDownWait)
    #save plots
    print('Saving IV plots...')
    plot.mainplt.savefig('{0}/IV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    timeplot.savefig('{0}/IV_timeplot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    timeplot.close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
   
    return status

 
def measureCV(ps,lcr,save_path,Vinitial,Vstart,Vfinal,Vstep_initiate,Vstep_run,full_step,ramp_down,kill_on_hit_comp,rest_time,first_point_rest_time, lcrFrequencies):
    # Peform CV test using power supply, ps, and lcr meter, lcr. 
   
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=1.0 #V
    rampDownWait=0.5 #s
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    
    #Setdata file
    data = open(save_path, 'a')
    #data.write('#Date-Time,Voltage(V),Current(A),Temperature(C),Humidity(%)\n')
    data.write('#Date-Time Voltage(V) Current(A) Capacitance(F) Resistance(Ohm) Frequency (kHz)\n')
    print('{0} created successfully...'.format(save_path))

    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = CVPlotWindow()
    plot.open()
    
    print("Setup complete- beginning test")

    try:

        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        if fabs(Vstart-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",Vstart,"Measured starting voltage=", voltageCheck)
            raiseError("Initial voltage did not match that requested, aborting")
                  
        print(Vstart,Vfinal,Vstep_run)
        for targetVoltage in np.arange(Vstart,Vfinal+Vstep_run,Vstep_run):
            print("Stepping to voltage",targetVoltage)
            #set voltage, check we don't hit compliance
            ps.setVoltage(targetVoltage)
            print("Checking compliance")
            if ps.hitCompliance(5):
                raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))

            time.sleep(rest_time)
            
            #begin measurement
            for frequency in lcrFrequencies:
            
                #set LCR frequency
                lcr.setFrequency(frequency)
                time.sleep(0.5) #wait to make sure frequency has been updated?
                voltage, current = ps.readVoltageAndCurrent()
                capacitance = lcr.readCapacitance()
                resistance = lcr.readResistance()
                
                #check voltage makes sense
                if fabs(targetVoltage-voltage)>voltageTolerance:
                    print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                    raiseError("Measured voltage does not match that observed, aborting run")
                
               
                date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
                measurement = [date_time, voltage, current, capacitance, resistance, (str)(frequency/1000.0)]
                measurement = [(str)(x) for x in measurement]
                data.write(' '.join(measurement) + '\n')
                plot.update(measurement)
                print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

         
     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    ps.controlSource('off')
    #save plots
    print('Saving CV plots...')
    plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
    
    return status


def measureInterstripCV_Ioannis(ps,am,lcr,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,am_Vfinal,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time,lcrFrequencies):

    # CV test using two power supplies: ps is ramped to a fixed voltage for the test and ramped down after again, am performs IV sweep and ramps down after. 
    
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=1.0 #V
    rampDownWait=0.5 #s
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    
    #Setdata file
    data = open(save_path, 'a')
    data.write('#Date-Time Voltage(V) Current(A) Capacitance(F) Resistance(Ohm) Frequency (kHz)\n')

    print('{0} created successfully...'.format(save_path))

    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = CVPlotWindow()
    plot.open()


    print("Setup complete- beginning test")

    try:
    
        #ramp HV Bias
        successfulRamp=RampVoltage(ps,ps_Vinitial,ps_Vfinal,ps_Vstep)
        if successfulRamp==False:
            raiseError("Failed to reach target bias voltage")
            
        #ramp LV to starting point
        successfulRamp=RampVoltage(am,0.0,am_Vinitial,am_Vstep)
        if successfulRamp==False:
            raiseError("Failed to reach starting low voltage")
    
            
            
        print("Waiting for",first_point_rest_time,"s before starting measurements")
        time.sleep(first_point_rest_time)        

        #ramp LV and do measurement
        voltageCheck=float(am.readVoltageAndCurrent()[0])
        if fabs(am_Vinitial-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",am_Vinitial,"Measured starting voltage=", voltageCheck)
            raiseError("Initial voltage did not match that requested, aborting")
        
        print(am_Vinitial,am_Vfinal,am_Vstep)
        for targetVoltage in np.arange(am_Vinitial,am_Vfinal+am_Vstep,am_Vstep):
            print("Stepping to voltage",targetVoltage)
            time.sleep(rest_time)
            #set voltage, check we don't hit compliance
            am.setVoltage(targetVoltage)
            print("Checking compliance")
            if am.hitCompliance(5):
                raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))
            
            #begin measurement
            for frequency in lcrFrequencies:
            
                #set LCR frequency
                lcr.setFrequency(frequency)
                time.sleep(0.5) #wait to make sure frequency has been updated?
                voltage, current = am.readVoltageAndCurrent()
                capacitance = lcr.readCapacitance()
                resistance = lcr.readResistance()
                
                #check voltage makes sense
                if fabs(targetVoltage-voltage)>voltageTolerance:
                    print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                    raiseError("Measured voltage does not match that observed, aborting run")
                     
                
                date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
                measurement = [date_time, voltage, current, capacitance, resistance, (str)(frequency/1000.0)]
                measurement = [(str)(x) for x in measurement]
                data.write(' '.join(measurement) + '\n')
                plot.update(measurement)
                print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    RampDown(am,rampDownStep,rampDownWait)
    #save plots
    print('Saving CV plots...')
    plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
   
    return status

def measureInterstripCV_Phil(ps,am,lcr,save_path,ps_Vstep,ps_Vinitial,ps_Vfinal,am_Vstep,am_Vinitial,full_step,ramp_down,kill_on_hit_compliance,rest_time,first_point_rest_time,lcrFrequencies):

    # CV test using two power supplies: ps is ramped to a fixed voltage for the test and ramped down after again, am performs IV sweep and ramps down after. 
    
    #Define fixed parameters- compliance check attemps, step sizes, file names
    voltageTolerance=0.01 #V
    rampDownStep=1.0 #V
    rampDownWait=0.5 #s
    nComplianceChecks=5
    status=0 #0=success, 1=fail
    
    temperature=0
    humidity=0
    
    
    #Setdata file
    data = open(save_path, 'a')
    data.write('#Date-Time Voltage(V) Current(A) Capacitance(F) Resistance(Ohm) Frequency (kHz)\n')

    print('{0} created successfully...'.format(save_path))

    #Construct our PlotWindow object and open the display
    print('Opening plot window...')
    plot = CVPlotWindow()
    plot.open()


    print("Setup complete- beginning test")

    try:
    
  
        #ramp LV to initial voltage, should be 0...
        successfulRamp=RampVoltage(am,0.0,am_Vinitial,am_Vstep)
        if successfulRamp==False:
            raiseError("Failed to reach starting low voltage")
    
           
            
        print("Waiting for",first_point_rest_time,"s before starting measurements")
        time.sleep(first_point_rest_time)        

        #ramp LV and do measurement
        voltageCheck=float(ps.readVoltageAndCurrent()[0])
        if fabs(ps_Vinitial-voltageCheck)>voltageTolerance:
            print("Target starting voltage:",am_Vinitial,"Measured starting voltage=", voltageCheck)
            raiseError("Initial voltage did not match that requested, aborting")
        
        print(ps_Vinitial,ps_Vfinal,ps_Vstep)
        for targetVoltage in np.arange(ps_Vinitial,ps_Vfinal+ps_Vstep,ps_Vstep):
            print("Stepping to voltage",targetVoltage)
            time.sleep(rest_time)
            #set voltage, check we don't hit compliance
            ps.setVoltage(targetVoltage)
            print("Checking compliance")
            if ps.hitCompliance(5):
                raiseError("PS has hit compliance at voltage:{} aborting run".format(targetVoltage))
            
            #begin measurement
            for frequency in lcrFrequencies:
            
                #set LCR frequency
                lcr.setFrequency(frequency)
                time.sleep(0.5) #wait to make sure frequency has been updated?
                voltage, current = ps.readVoltageAndCurrent()
                capacitance = lcr.readCapacitance()
                resistance = lcr.readResistance()
                
                #check voltage makes sense
                if fabs(targetVoltage-voltage)>voltageTolerance:
                    print("Target voltage:",targetVoltage,"Measured  voltage=", voltage)
                    raiseError("Measured voltage does not match that observed, aborting run")
                     
                
                date_time = time.strftime('%Y/%m/%d-%H:%M:%S')
                measurement = [date_time, voltage, current, capacitance, resistance, (str)(frequency/1000.0)]
                measurement = [(str)(x) for x in measurement]
                data.write(' '.join(measurement) + '\n')
                plotMeasurement = [date_time, voltage, capacitance, current, resistance, (str)(frequency/1000.0)]
                plotMeasurement = [(str)(x) for x in plotMeasurement]

                plot.update(plotMeasurement)
                print('At {0}: V = {1} V, I = {2} A, C = {3} F, R = {4} Ohms, F = {5} kHz.'.format(*measurement))

     
    except Exception as e:
        print(e)
        status=1
    
    #ramp down power supply and turn off output
    RampDown(ps,rampDownStep,rampDownWait)
    RampDown(am,rampDownStep,rampDownWait)
    #save plots
    print('Saving CV plots...')
    plot.mainplt.savefig('{0}/CV_plot_{1}.png'.format(os.getcwd(), time.strftime('%Y%m%d-%H%M%S')))
    print('Closing {0}...'.format(save_path))
    data.close()
    plot.close()
    
    print('Measurement finished at: {0}.'.format(time.strftime('%Y/%m/%d-%H:%M:%S')))
   
    return status

def threadingTestFunction(frame):  
    while frame.abortTest==False:
        print("I am still running, abort test=",frame.abortTest)
        time.sleep(1)
    print("Run aborted")  
    frame.b_run.Enable()
    


if __name__ == '__main__':
    pass




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
                pltData.write(voltage + ',' + current + ",   " + date_time + ",   " + comment + '\n')
    
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