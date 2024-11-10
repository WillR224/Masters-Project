#!/usr/bin/python
# Devices.py -- contains class wrappers for measurement instruments (Keithley 2410, Keithley 6487, Keithley 6517, KeysightE4980AL, WayneKerr 6500B LCR)
# Updated: 01/03/2021
# Contributing: Matt Basso (University of Toronto), Will George (University of Birmingham)

from Interfaces import GPIB
from Interfaces import Serial
from Interfaces import Socket
from math import fabs
import numpy as np
import time
import pyvisa as visa

# Relevant for controlling Xilab stepper motors
from ctypes import *
import time
import os
import sys
import platform
import tempfile
import re


if sys.version_info >= (3,0):
    import urllib.parse

# Dependences
    
# For correct usage of the library libximc,
# you need to add the file pyximc.py wrapper with the structures of the library to python path.
cur_dir = os.path.abspath(os.path.dirname(__file__)) # Specifies the current directory.
#ximc_dir = os.path.join(cur_dir, "..", "..", "..", "ximc") # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
ximc_dir = os.path.join(cur_dir, "ximc") # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python") # Formation of the directory name with python dependencies.
sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path

# Depending on your version of Windows, add the path to the required DLLs to the environment variable
# bindy.dll
# libximc.dll
# xiwrapper.dll
if platform.system() == "Windows":
    # Determining the directory with dependencies for windows depending on the bit depth.
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32" # 
    libdir = os.path.join(ximc_dir, arch_dir)
    if sys.version_info >= (3,8):
        os.add_dll_directory(libdir)
    else:
        os.environ["Path"] = libdir + ";" + os.environ["Path"] # add dll path into an environment variable

try: 
    from pyximc import *
except ImportError as err:
    print ("Can't import pyximc module. The most probable reason is that you changed the relative location of the test_Python.py and pyximc.py files. See developers' documentation for details.")
    exit()
except OSError as err:
    # print(err.errno, err.filename, err.strerror, err.winerror) # Allows you to display detailed information by mistake.
    if platform.system() == "Windows":
        if err.winerror == 193:   # The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.
            print("Err: The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.")
            # print(err)
        elif err.winerror == 126: # One of the library bindy.dll, libximc.dll, xiwrapper.dll files is missing.
            print("Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing.")
            print("It is also possible that one of the system libraries is missing. This problem is solved by installing the vcredist package from the ximc\\winXX folder.")
            # print(err)
        else:           # Other errors the value of which can be viewed in the code.
            print(err)
        print("Warning: If you are using the example as the basis for your module, make sure that the dependencies installed in the dependencies section of the example match your directory structure.")
        print("For correct work with the library you need: pyximc.py, bindy.dll, libximc.dll, xiwrapper.dll")
    else:
        print(err)
        print ("Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")
    exit()
    
    
    

class Keithley2410(Serial):

    __slots__ = ['compliance', 'average']

    def __init__(self, port, compliance, average = 1):
        super(Keithley2410, self).__init__(port)
        self.compliance = compliance
        self.average    = average

    def setup(self):
        self.open()
        self.sendCommand(':SOUR:FUNC VOLT')
        self.sendCommand(':SOUR:VOLT:RANGE 1100')
        #self.sendCommand(':SENS:CURR:RANG:AUTO ON')
        self.sendCommand(':SENS:CURR:RANG:AUTO OFF')
        #self.sendCommand(':SENS:CURR:RANG ' + str(self.compliance))
        self.sendCommand(':SENS:CURR:PROT ' + str(self.compliance))
        self.sendCommand(':SENS:FUNC:CONC OFF')
        self.sendCommand(':SENS:FUNC:ON "CURR"')
        self.sendCommand(':FORM:ELEM VOLT, CURR')
        self.sendCommand(':SENS:AVER:STAT OFF')
        if self.average > 1:
            self.sendCommand(':SENS:AVER:TCON REP')
            self.sendCommand(':SENS:AVER:COUN ' + str(self.average))
            self.sendCommand(':SENS:AVER:STAT ON')
        else:
            pass

    def setVoltage(self, voltage):
        self.sendCommand(':SOUR:VOLT ' + str(voltage))


    def readVoltageAndCurrent(self):
        ''' This function performs manual averaging in addition to that done internally by the instrument. '''
        n_av = 5
        voltage = 0.0
        current = 0.0
        for i in range(0,n_av):
            self.sendCommand('READ?')
            while True:
                data = self.getData()
                if data == '':
                    continue
                else:
                    break
            tmp_voltage, tmp_current = data.split(',')[0:2]
            voltage += float(tmp_voltage)
            current += float(tmp_current)
            time.sleep(0.05)
        av_voltage = voltage/n_av
        av_current = current/n_av
        return av_voltage, av_current

    def triggerRead(self):
        self.sendCommand('READ?')

    def readVoltageAndCurrentFromBuffer(self):
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        voltage, current = data.split(',')[0:2]
        return voltage, current

    def inCompliance(self):
        self.sendCommand(':SENS:CURR:PROT:TRIP?')
        while True:
            in_complicance = self.getData()
            if in_complicance == '':
                continue
            else:
                break
        if in_complicance == '1':
            return True
        else:
            return False
    
    def hitCompliance(self, attempts):
        
        fails=0
        for N in range(attempts):
            self.sendCommand(':SENS:CURR:PROT:TRIP?')
            while True:
                in_compliance = self.getData()
                if in_compliance == '':
                    continue
                else:
                    break
            if in_compliance == '1':
                break
            else: 
                fails+=1    
        
        if fails>=attempts:
            return False
        else:
            return True

    def controlSource(self, state):
        if state == 'on':
            self.sendCommand('OUTP:STAT 1')
        elif state == 'off':
            self.sendCommand('OUTP:STAT 0')
        else:
            pass

    def controlAverage(self, state):
        if self.average > 1:
            if state == 'on':
                self.sendCommand(':SENS:AVER:STAT ON')
            elif state == 'off':
                self.sendCommand(':SENS:AVER:STAT OFF')
            else:
                pass
        else:
            pass

    def controlAutoRange(self, state):
        if state == 'on':
            self.sendCommand(':SENS:CURR:RANG:AUTO ON')
        elif state == 'off':
            self.sendCommand(':SENS:CURR:RANG:AUTO OFF')
        else:
            pass

    def setCurrentRange(self, range):
        self.sendCommand(':SENS:CURR:RANG ' + str(range))

    def setAverage(self, average):
        self.average = average
        self.sendCommand(':SENS:AVER:COUN ' + str(self.average))

    def getAverage(self):
        self.sendCommand(':SENS:AVER:COUN?')
        while True:
            av_tmp = self.getData()
            if av_tmp == '':
                continue
            else:
                break
        return av_tmp
        #return self.average

    def setCompliance(self, compliance):
        self.compliance = compliance
        self.sendCommand(':SENS:CURR:PROT ' + str(self.compliance))

    def shutdown(self):
        self.close()

class Keithley2470(GPIB):

    __slots__ = ['compliance', 'average']

    def __init__(self, port, compliance, average = 1):
        super(Keithley2470, self).__init__(port)
        self.compliance = compliance
        self.average    = average

    def setup(self):
        self.open()
        self.sendCommandWriteOnly(':SOUR:FUNC VOLT') 
        self.sendCommandWriteOnly(':SOUR:VOLT:RANGE 500')
        self.sendCommandWriteOnly(':SOUR:VOLT:READ:BACK 0') #sets voltage measurement to return what it sources, not what it measures back
        self.sendCommandWriteOnly(':SENS:CURR:RANG:AUTO ON')
        self.sendCommandWriteOnly(':SOUR:VOLT:ILIM ' + str(self.compliance)) #sets current limit when acting as voltage source
        self.sendCommandWriteOnly(':SENS:FUNC "CURR"')
        self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT OFF')
        if self.average > 1:
            self.sendCommandWriteOnly(':SENS:CURR:AVER:TCON REP')
            self.sendCommandWriteOnly(':SENS:CURR:AVER:COUN ' + str(self.average))
            self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT ON')
        else:
            pass

    def setVoltage(self, voltage):
        self.sendCommandWriteOnly(':SOUR:VOLT ' + str(voltage))

    def readCurrent(self):
        ''' This function performs manual averaging in addition to that done internally by the instrument. '''
        n_av = 5
        voltage = 0.0
        current = 0.0
        for i in range(0,n_av):
            self.sendCommandWriteRead('READ?')
            while True:
                data = self.getData()
                if data == '':
                    continue
                else:
                    break
            tmp_current = data
            current += float(tmp_current)
            time.sleep(0.05)
        av_current = current/n_av
        return str(av_current)
        
        
    def readVoltageAndCurrent(self):
        ''' This function performs manual averaging in addition to that done internally by the instrument. '''
        n_av = 5
        voltage = 0.0
        current = 0.0
        for i in range(0,n_av):
            self.sendCommandWriteRead('READ? "defbuffer1", SOUR, READ')
            while True:
                data = self.getData()
                if data == '':
                    continue
                else:
                    break
            tmp_voltage, tmp_current = data.split(',')[0:2]
            voltage += float(tmp_voltage)
            current += float(tmp_current)
            time.sleep(0.05)
        av_voltage = voltage/n_av
        av_current = current/n_av
        return av_voltage, av_current
        
    def triggerRead(self):
        self.sendCommandWriteRead('READ? "defbuffer1", SOUR, READ')

    def readVoltageAndCurrentFromBuffer(self):
        #print("Warning, readVoltageAndCurrentFromBuffer not yet implemented for 2470, running readVoltageAndCurrent instead")
        #voltage, current = self.readVoltageAndCurrent()
        #return voltage, current
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        voltage, current = data.split(',')[0:2]
        return voltage, current

    def inCompliance(self):
        self.sendCommandWriteRead(':SOUR:VOLT:ILIM:TRIP?')
        while True:
            in_complicance = self.getData()
            #print ("In compliance = ",in_complicance)
            if in_complicance == '':
                continue
            else:
                break
        
        if in_complicance == '1\n':
            print ("Compliance =1")
            return True
        else:
            return False
            
            
    def hitCompliance(self, attempts):
        
        fails=0
        for N in range(attempts):
            self.sendCommand(':SOUR:VOLT:ILIM:TRIP?')
            while True:
                in_compliance = self.getData()
                if in_compliance == '':
                    continue
                else:
                    break
            if in_compliance == '1\n':
                break    
            else: 
                fails+=1
        
        if fails>=attempts:
            return False
        else:
            return True            

    def controlSource(self, state):
        if state == 'on':
            self.sendCommandWriteOnly('OUTP:STAT 1')
        elif state == 'off':
            self.sendCommandWriteOnly('OUTP:STAT 0')
        else:
            pass

    def controlAverage(self, state):
        if self.average > 1:
            if state == 'on':
                self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT ON')
            elif state == 'off':
                self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT OFF')
            else:
                pass
        else:
            pass

    def controlAutoRange(self, state):
        if state == 'on':
            self.sendCommandWriteOnly(':SENS:CURR:RANG:AUTO ON')
        elif state == 'off':
            self.sendCommandWriteOnly(':SENS:CURR:RANG:AUTO OFF')
        else:
            pass

    def setCurrentRange(self, range):
        self.sendCommandWriteOnly(':SENS:CURR:RANG ' + str(range))

    def setAverage(self, average):
        self.average = average
        self.sendCommandWriteOnly(':SENS:CURR:AVER:COUN ' + str(self.average))

    def getAverage(self):
        self.sendCommandWriteOnly(':SENS:CURR:AVER:COUN?')
        self.triggerRead()
        while True:
            av_tmp = self.getData()
            if av_tmp == '':
                continue
            else:
                break
        return av_tmp
        #return self.average

    def setCompliance(self, compliance):
        self.compliance = compliance
        self.sendCommandWriteOnly(':SOUR:VOLT:ILIM  ' + str(self.compliance))

    def shutdown(self):
        self.close()

class Keithley6487(GPIB):

    __slots__ = ['compliance', 'average']

    def __init__(self, device_id, compliance, average = 1):
        super(Keithley6487, self).__init__(device_id)
        self.compliance = compliance
        self.average    = average

    def setup(self):
        self.open()
        self.sendCommandWriteOnly(':SENS:FUNC \'CURR\'\n')
        self.sendCommandWriteOnly(':SENS:CURR:RANG:AUTO ON\n')
        self.sendCommandWriteOnly(':SOUR:VOLT:RANG 500\n')
        self.sendCommandWriteOnly(':SOUR:VOLT:ILIM ' + str(self.compliance))
        self.sendCommandWriteOnly(':ARM:SOUR IMM')
        self.sendCommandWriteOnly(':ARM:COUN 1')
        self.sendCommandWriteOnly(':FORM:ELEM READ, VSO') # ALL?
        self.sendCommandWriteOnly(':SENS:AVER:STAT OFF') #turn off averaging
        if self.average > 1:
            self.sendCommandWriteOnly(':SENS:AVER:TCON REP')
            self.sendCommandWriteOnly(':SENS:AVER:COUN ' + str(self.average))
            self.sendCommandWriteOnly(':SENS:AVER:STAT ON')
        else:
            pass

    def setVoltage(self, voltage):
        self.sendCommandWriteOnly(':SOUR:VOLT:IMM:AMPL ' + str(voltage))

    def setVoltageRange(self,Vrange):
        self.sendCommandWriteOnly(':SOUR:VOLT:RANG '+str(Vrange)+'\n')

    def readVoltageAndCurrent(self):
        self.sendCommandWriteRead('READ?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        current, term_voltage = data.split(',')[0:2]
        voltage = term_voltage.strip('\n')
        return voltage, current

    def triggerRead(self):
        self.sendCommandWriteRead('READ?')

    def readVoltageAndCurrentFromBuffer(self):
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        current, term_voltage = data.split(',')[0:2]
        voltage = term_voltage.strip('\n')
        return voltage, current

    def inCompliance(self):
        self.sendCommandWriteRead(':STAT:QUE:NEXT?') #read and clear oldest error message
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        if data.split(',')[0] == '+315': #V source compliance detected
            return True
        else:
            return False

    def controlSource(self, state):
        if state == 'on':
            self.sendCommandWriteOnly(':SOUR:VOLT:STAT 1')
        elif state == 'off':
            self.sendCommandWriteOnly(':SOUR:VOLT:STAT 0')
        else:
            pass

    def controlAverage(self, state):
        if self.average > 1:
            if state == 'on':
                self.sendCommandWriteOnly(':SENS:AVER:STAT ON')
            elif state == 'off':
                self.sendCommandWriteOnly(':SENS:AVER:STAT OFF')
            else:
                pass
        else:
            pass

    def setCurrentRange(self, range):
        self.sendCommandWriteOnly(':SENS:CURR:RANG ' + str(range))

    def setAverage(self, average):
        self.average = average
        self.sendCommandWriteOnly(':SENS:AVER:COUN ' + str(self.average))

    def hitCompliance(self, attempts):
        return False

    def setCompliance(self, compliance):
        self.compliance = compliance
        self.sendCommandWriteOnly(':SOUR:VOLT:ILIM ' + str(self.compliance))

    def shutdown(self):
        self.close()


class Keithley6517(GPIB): #Was GPIB

    __slots__ = ['compliance', 'average']

    #def __init__(self, port, compliance, average = 1):
        #super(Keithley6517, self).__init__(port)

    def __init__(self, device_id, compliance, average = 1):
        super(Keithley6517, self).__init__(device_id)
        self.compliance = compliance
        self.average    = average

    def setup(self):
        self.open()
        self.sendCommandWriteOnly(':SENS:FUNC \'CURR\'')
        self.sendCommandWriteOnly(':SENS:CURR:RANG:AUTO ON')
        #self.sendCommand(':SOUR:VOLT:RANG 10'); #anything below 100 sets voltage range to 100 V
        self.sendCommandWriteOnly(':SOUR:VOLT:RANG 1000')
        #For 100 V range, current compliance is 10mA
        self.sendCommandWriteOnly(':ARM:SOUR IMM')
        self.sendCommandWriteOnly(':ARM:COUN 1')
        self.sendCommandWriteOnly(':FORM:ELEM READ, VSO')
        self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT OFF')
        if self.average > 1:
            self.sendCommandWriteOnly(':SENS:CURR:AVER:TYPE SCAL')
            self.sendCommandWriteOnly(':SENS:CURR:AVER:TCON REP')
            self.sendCommandWriteOnly(':SENS:CURR:AVER:COUN ' + str(self.average))
            self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT ON')
        else:
            pass

    def setVoltage(self, voltage):
        self.sendCommandWriteOnly(':SOUR:VOLT:LEV:IMM:AMPL ' + str(voltage))

    def readVoltageAndCurrent(self):
        self.sendCommandWriteRead('READ?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        current, voltage = data.split(',')[0:2]
        return voltage, current

    def triggerRead(self):
        self.sendCommandWriteRead('READ?')

    def readVoltageAndCurrentFromBuffer(self):
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        current, voltage = data.split(',')[0:2]
        return voltage, current

    def inCompliance(self):
        self.sendCommandWriteRead(':STAT:QUE:NEXT?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        if data.split(',')[0] == '+315':
            return True
        else:
            return False

    def controlSource(self, state):
        if state == 'on':
            self.sendCommandWriteOnly(':OUTP:STAT ON') # or 'SOUR:VOLT:STAT 1'
        elif state == 'off':
            self.sendCommandWriteOnly(':OUTP:STAT OFF') # or 'SOUR:VOLT:STAT 0'
        else:
            pass

    def controlAverage(self, state):
        if self.average > 1:
            if state == 'on':
                self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT ON')
            elif state == 'off':
                self.sendCommandWriteOnly(':SENS:CURR:AVER:STAT OFF')
            else:
                pass
        else:
            pass

    def setCurrentRange(self, range):
        self.sendCommandWriteOnly(':SENS:CURR:RANG ' + str(range))

    def setAverage(self, average):
        self.average = average
        self.sendCommandWriteOnly(':SENS:CURR:AVER:COUN ' + str(self.average))

    #def setCompliance(self, compliance):
    #    print('Cannot set compliance for Keithley6517.')
    #    self.compliance = compliance
    #    self.sendCommandWriteOnly(':SOUR:VOLT:ILIM ' + str(self.compliance)) #
        
    def setCompliance(self, compliance):
        print('Cannot set compliance for Keithley6517.')
        
    def hitCompliance(self, attempts):
        return False

    def shutdown(self):
        self.close()

class Keithley6517_Serial(Serial): #Was GPIB

    __slots__ = ['compliance', 'average']

    #def __init__(self, port, compliance, average = 1):
        #super(Keithley6517, self).__init__(port)

    def __init__(self, device_id, compliance, average = 1):
        super(Keithley6517_Serial, self).__init__(device_id)
        self.compliance = compliance
        self.average    = average

    def setup(self):
        self.open()
        self.sendCommand(':SENS:FUNC \'CURR\'')
        self.sendCommand(':SENS:CURR:RANG:AUTO ON')
        #self.sendCommand(':SOUR:VOLT:RANG 10'); #anything below 100 sets voltage range to 100 V
        self.sendCommand(':SOUR:VOLT:RANG 1000')
        #For 100 V range, current compliance is 10mA
        self.sendCommand(':ARM:SOUR IMM')
        self.sendCommand(':ARM:COUN 1')
        self.sendCommand(':FORM:ELEM READ, VSO')
        self.sendCommand(':SENS:CURR:AVER:STAT OFF')
        if self.average > 1:
            self.sendCommand(':SENS:CURR:AVER:TYPE SCAL')
            self.sendCommand(':SENS:CURR:AVER:TCON REP')
            self.sendCommand(':SENS:CURR:AVER:COUN ' + str(self.average))
            self.sendCommand(':SENS:CURR:AVER:STAT ON')
        else:
            pass

    def setVoltage(self, voltage):
        self.sendCommand(':SOUR:VOLT:LEV:IMM:AMPL ' + str(voltage))

    def readVoltageAndCurrent(self):
        self.sendCommand('READ?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        current, voltage = data.split(',')[0:2]
        return voltage, current

    def triggerRead(self):
        self.sendCommand('READ?')

    def readVoltageAndCurrentFromBuffer(self):
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        current, voltage = data.split(',')[0:2]
        return voltage, current

    def inCompliance(self):
        self.sendCommand(':STAT:QUE:NEXT?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        if data.split(',')[0] == '+315':
            return True
        else:
            return False

    def controlSource(self, state):
        if state == 'on':
            self.sendCommand(':OUTP:STAT ON') # or 'SOUR:VOLT:STAT 1'
        elif state == 'off':
            self.sendCommand(':OUTP:STAT OFF') # or 'SOUR:VOLT:STAT 0'
        else:
            pass

    def controlAverage(self, state):
        if self.average > 1:
            if state == 'on':
                self.sendCommand(':SENS:CURR:AVER:STAT ON')
            elif state == 'off':
                self.sendCommand(':SENS:CURR:AVER:STAT OFF')
            else:
                pass
        else:
            pass

    def setCurrentRange(self, range):
        self.sendCommand(':SENS:CURR:RANG ' + str(range))

    def setAverage(self, average):
        self.average = average
        self.sendCommand(':SENS:CURR:AVER:COUN ' + str(self.average))

    #def setCompliance(self, compliance):
    #    print('Cannot set compliance for Keithley6517.')
    #    self.compliance = compliance
    #    self.sendCommandWriteOnly(':SOUR:VOLT:ILIM ' + str(self.compliance)) #
        
    def setCompliance(self, compliance):
        print('Cannot set compliance for Keithley6517.')
        
    def hitCompliance(self, attempts):
        return False

    def shutdown(self):
        self.close()

class KeysightE4980AL(GPIB):

    __slots__ = ['frequency', 'level', 'average']

    # Init class for ethernet 
    #def __init__(self, ip, port, frequency, level = 1., average = 1):
    #    super(KeysightE4980AL, self).__init__(ip, port)
    
    def __init__(self, device_id, frequency, level = 1., average = 1):
        super(KeysightE4980AL, self).__init__(device_id)
        self.frequency  = frequency
        self.level      = level
        self.average    = average


    def setup(self):
        self.open()
        self.sendCommandWriteOnly(':DISP:PAGE MEAS')
        self.sendCommandWriteOnly(':FUNC:IMP:TYPE CPRP')
        self.sendCommandWriteOnly(':FREQ ' + str(self.frequency))
        self.sendCommandWriteOnly(':VOLT:LEV ' + str(self.level))
        self.sendCommandWriteOnly(':FUNC:IMP:RANG:AUTO ON')
        self.sendCommandWriteOnly(':BIAS:VOLT:LEV 0')
        self.sendCommandWriteOnly(':TRIG:SOUR BUS')
        self.sendCommandWriteOnly(':TRIG:DEL 0')
        self.sendCommandWriteOnly(':TRIG:TDEL 0')
        self.sendCommandWriteOnly(':APER MED,' + str(self.average))
        self.sendCommandWriteOnly(':CORR:LENG 2')
        self.sendCommandWriteOnly(':CORR:LOAD:TYPE CPD')
        self.sendCommandWriteOnly(':CORR:METH SING')
        self.sendCommandWriteOnly(':CORR:OPEN:STAT ON')
        self.sendCommandWriteOnly(':CORR:SHOR:STAT OFF')
        self.sendCommandWriteOnly(':CORR:LOAD:STAT OFF')

    def openCorrection(self):
        self.sendCommandWriteOnly(':CORR:OPEN:EXEC')
        time.sleep(35.)
        #return True

    def openCorrectionToggle(self,state):
        if state == 'on':
            self.sendCommandWriteOnly('CORR:OPEN:STAT ON')
        elif state == 'off':
            self.sendCommandWriteOnly('CORR:OPEN:STAT OFF')
        else:
            pass

    def shortCorrectionToggle(self,state):
        if state == 'on':
            self.sendCommandWriteOnly(':CORR:SHOR:STAT ON')
        elif state == 'off':
            self.sendCommandWriteOnly(':CORR:SHOR:STAT OFF')
        else:
            pass

    def shortCorrection(self): #doSCTrim
        self.sendCommandWriteOnly(':CORR:SHOR:EXEC')
        time.sleep(35.)
        #return True

    def readCapacitance(self):
        self.sendCommandWriteOnly(':TRIG:IMM')
        self.sendCommandWriteRead(':FETC?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        capacitance = data.split(',')[0]
        return capacitance

    def readResistance(self):
        self.sendCommandWriteOnly(':TRIG:IMM')
        self.sendCommandWriteRead(':FETC?')
        while True:
            data = self.getData()
            if data == '':
                continue
            else:
                break
        resistance = data.split(',')[1]
        return resistance

    def triggerRead(self):
        self.sendCommandWriteOnly(':TRIG:IMM')
        self.sendCommandWriteRead(':FETC?')

    def readCapacitanceFromBuffer(self):
        while True:
            data = self.getData().split(',')
            if data == ['']:
                continue
            else:
                break
        capacitance = data[0]
        return capacitance

    def readResistanceFromBuffer(self):
        while True:
            data = self.getData().split(',')
            if data == ['']:
                continue
            else:
                break
        resistance = data[1]
        return resistance

    def readCapacitanceAndResistanceFromBuffer(self):
        while True:
            data = self.getData().split(',')
            if data == ['']:
                continue
            else:
                break
        capacitance = data[0]
        resistance = data[1]
        return capacitance, resistance

    def controlAverage(self, state):
        if state == 'on':
            self.sendCommandWriteOnly(':APER MED,' + str(self.average))
        elif state == 'off':
            self.sendCommandWriteOnly(':APER MED,1')
        else:
            pass

    def setFrequency(self, frequency):
        self.frequency = frequency
        self.sendCommandWriteOnly(':FREQ ' + str(self.frequency))

    def setLevel(self, level):
        self.level = level
        self.sendCommandWriteOnly(':VOLT:LEV ' + str(self.level))

    def setAverage(self, average):
        self.average = average
        self.sendCommandWriteOnly(':APER MED,' + str(self.average))

    def setEquivCirc(self, equiv_circuit):
        if equiv_circuit == 0:
            self.sendCommandWriteOnly(':FUNC:IMP:TYPE CPRP')
        elif equiv_circuit == 1:
            self.sendCommandWriteOnly(':FUNC:IMP:TYPE CSRS')

    def setFunctionType(self,lcrCircuit):
        if lcrCircuit == 'CSRS':
            self.sendCommandWriteOnly(':FUNC:IMP:TYPE CSRS')
        elif lcrCircuit == 'CPRP':
            self.sendCommandWriteOnly(':FUNC:IMP:TYPE CPRP')
        else:
            print('Invalid circuit type')

    def shutdown(self):
        self.close()


class WayneKerr6500B(GPIB):


    __slots__ = ['frequency', 'level', 'average']

    def __init__(self, device_id, frequency, level = 1., average = 1):
        super(WayneKerr6500B, self).__init__(device_id)
        self.frequency  = frequency
        self.level      = level
        self.average    = average

    def setup(self):
        self.open()
        self.sendCommandWriteOnly(':METER:DISP ABS')
        self.sendCommandWriteOnly(':METER:FUNC:1 C;2 R')
        self.sendCommandWriteOnly(':METER:EQU-CCT PAR')
        self.sendCommandWriteOnly(':METER:FREQ ' + str(self.frequency))
        self.sendCommandWriteOnly(':METER:LEVEL ' + str(self.level) + 'V')
        self.sendCommandWriteOnly(':METER:RANGE AUTO')
        self.sendCommandWriteOnly(':METER:BIAS-TYPE VOL')
        self.sendCommandWriteOnly(':METER:BIAS 0')
        self.sendCommandWriteOnly(':METER:SPEED FST') 
        # Add command to set average here if WK has averaging.
        # From WK4235 manual (not sure if this will work for 6500B): self.sendCommand(':CAL:HF-CAL') 


    def openCorrection(self):
        self.doOCTrim()
        time.sleep(35.)
        #return True

    def doOCTrim(self):
        response = self.sendCommandWithWait(':CAL:OC-TRIM') #returns 0 if CAL fails, need a check?
        if(response == '1'):
            return True
        elif(response == '0'):
            return False
        return False


    def shortCorrection(self): #doSCTrim
        self.doSCTrim()
		
    def doSCTrim(self):
        self.sendCommandWriteOnly(':CAL:SC-TRIM')
        time.sleep(30.)

    def readCapacitance(self):
        capacitance = 0.0
        n_av = 3
        for i in range(0,n_av):
            self.sendCommand(':METER:TRIG')
            while True:
                data = self.getData()
                #print('Capacitance = ',data)
                if data == '':
                    continue
                else:
                    break
            capacitance += float(data[0])
            time.sleep(0.05)
        av_capacitance = capacitance/n_av
        return str(av_capacitance)

    def readCapacitanceOnce(self):
        self.sendCommand(':METER:TRIG')
        while True:
            data = self.getData()
            print('Capacitance = ' + data[0])
            if data == '':
                continue
            else:
                break
        capacitance = data[0]
        return capacitance

    def readResistance(self):
        resistance = 0.0
        n_av = 3
        for i in range(0,n_av):
            self.sendCommand(':METER:TRIG')
            while True:
                data = self.getData()
                if data == '':
                    continue
                else:
                    break
            resistance += float(data[1])
            time.sleep(0.05)
        av_resistance = resistance/n_av
        return str(av_resistance)

    def readResistanceOnce(self):
        self.sendCommand(':METER:TRIG')
        while True:
            data = self.getData()
            #print('Resistance = ' + data[1])
            if data == '':
                continue
            else:
                break
        resistance = data[1]
        return resistance

    def triggerRead(self):
        self.sendCommand(':METER:TRIG')

    def readCapacitanceFromBuffer(self):
        while True:
            data = self.getData()
            if data == ['']:
                continue
            else:
                break
        capacitance = data[0]
        return capacitance

    def readResistanceFromBuffer(self):
        while True:
            data = self.getData()
            if data == ['']:
                continue
            else:
                break
        resistance = data[1]
        return resistance

    def controlAverage(self, state):
        #print("Warning, built in averaging not setup for WK yet, check documentation. Sending :METER:SPEED FST")
        if state == 'on':
            self.sendCommandWriteOnly(':METER:SPEED FST')
            #command to set averaging to str(self.average) here
        elif state == 'off':
            self.sendCommandWriteOnly(':METER:SPEED FST')
            #command to turn off averaging here (set to 1)
        else:
            pass

    def setFrequency(self, frequency):
        self.frequency = frequency
        self.sendCommandWriteOnly(':METER:FREQ ' + str(self.frequency))

    def setLevel(self, level):
        self.level = level
        self.sendCommandWriteOnly(':METER:LEVEL ' + str(self.level) + 'V')

    def setAverage(self, average):
        #print("Warning, built in averaging not setup for WK yet, check documentation. Sending :METER:SPEED FST")
        self.average = average
        self.sendCommandWriteOnly(':METER:SPEED FST')
        #command to set averaging to str(self.average) here

    def setEquivCirc(self, equiv_circuit):
        if equiv_circuit == 0:
            self.sendCommandWriteOnly(':METER:EQU-CCT PAR')
        elif equiv_circuit == 1:
            self.sendCommandWriteOnly(':METER:EQU-CCT SER')
			
    def setFunctionType(self,lcrCircuit):
        if lcrCircuit == 'CSRS':
            self.sendCommandWriteOnly(':METER:EQU-CCT SER')
        elif lcrCircuit == 'CPRP':
            self.sendCommandWriteOnly(':METER:EQU-CCT PAR')
        else:
            print('Invalid circuit type')
		

    def shutdown(self):
        self.close()



#I am sure that this will be wrong, but I want to try at least to create this as a class
#as a start to contain all the functions even if the inheritance is not done correctly

#Oscilloscope
class AgilentMSO9254A():
    
    device = None
    visaName = ""
    #def __init__(self, port, compliance, average = 1):
        #super(Keithley6517, self).__init__(port)t)

    def __init__(self, _visaName):
        self.visaName = _visaName

    def setup(self):
        rm = visa.ResourceManager()
        self.device = rm.get_instrument(self.visaName)  
        
    def reset(self):
        self.device.write('*RST')
        
    def setTimeBase(self, rng, delay):
        self.device.write(':TIMebase:SCALe ' + str(rng) + '')
        self.device.write(':TIMebase:DELay ' + str(delay) + '')
           
    def setChannelSettings(self, channelNum, scale, offset):
    
    
        self.device.write(':CHANnel' + str(channelNum) + ':DISPlay ON')
        self.device.write(':CHANnel' + str(channelNum) + ':SCALe ' + str(scale) + '')
        self.device.write(':CHANnel' + str(channelNum) + ':OFFSet ' + str(offset) + '')

    def setTriggerAuto(self):
        self.device.write(':TRIGger:SWEep AUTO')
    def setTriggerEd(self):
        self.device.write(':TRIGger:SWEep TRIGgered')
    def setTriggerChannel(self, channelNum):
        #NOT WORKING. SWAP CHANNELS OVER
        
        #chn = self.device.write(':TRIGger:COMM:SOURce?')
        time.sleep(2)
        #print("chn = " + str(chn))
        #self.device.write(':TRIGger:AND:ENABLe ON')
        #print("Trig And Enable")
        #time.sleep(5)
        #self.device.write(':TRIGger:COMM:SOURce CHAN2')
        #print("Trig CH2")
        #self.device.write(':TRIGger:AND:SOURce CHAN2, HIGH')
        #print("Trig CH2 HIGH")
        #chn = self.device.write(':TRIGger:COMM:SOURce?')
        #print("chn = " + str(chn))
    def setTriggerLevel(self, channelNum, level):
        #self.device.write(':TRIGger:LEVel CHAN2')
        self.device.write(':TRIGger:LEVel CHAN' + str(channelNum) + ',' + str(level) +'')
    def setTriggerMode(self):
        #Just some defaults for now
        self.device.write(':TRIGger:MODE EDGE')
        self.device.write(':TRIGger:EDGE:SLOPe POSitive')
       
    def singleMeasurement(self):
        self.device.write(':SINGle')
    def triggered(self):
        #print("State?")
        try:
            result = self.device.query(':ASTate?')
            time.sleep(0.2)
            #print("Result = '" + str(result) + "'")
            if str(result) == "ADONE" or str(result) == "ADONE\n" or str(result) == "ADONE\r":
                return True
            else:
                return False
        except Exception as e:
            print("triggered() failed with exception: ")
            print(e)
            return False
        
    def saveWaveformXY(self, path):
        #bump = ""
        try:
            self.device.write(':DISK:SAVE:WAVeform ALL,\"' + str(path) + '\",CSV,ON')
            #:DISK:SAVE:WAVeform\sALL,"C:\\FILE1",CSV,ON
            #self.device.write(':DISK:SAVE:WAVeform ALL,\"C:\\FILE2\",CSV,ON')
        except Exception as e:
            print("saveWaveformXY() failed with exception: ")
            print(e)
            return False
    def saveScreenGrab(self, path):
        try:
            self.device.write(':DISK:SAVE:IMAGe \"' + str(path) + '\",PNG')
        except Exception as e:
            print("saveScreenGrab() failed with exception: ")
            print(e)
            return False
        
    def mkdir(self, path):
        try:
            self.device.write(':DISK:MDIRectory \"' + str(path) + '\"')
        except Exception as e:
            print("mkdir() failed with exception: ")
            print(e)
            return False

    #def shutdown(self):
    #    self.close()
    
class MX180TP(Serial):

    __slots__ = ['compliance', 'average']

    def __init__(self, port, compliance, average = 1):
        super(MX180TP, self).__init__(port)
        self.compliance = compliance
        self.average    = average

    def setup(self):
        self.open()
        
    def reset(self):
        self.sendCommand('*RST\n')

    def setVoltage(self, channel, voltage):
        self.sendCommand('V' + str(channel) + ' ' + str(voltage) + '\n')
        
    def setCurrentLimit(self, channel, current):
        self.sendCommand('I' + str(channel) + ' ' + str(current) + '\n')
        
    def controlSource(self, channel, state):
        if state == 'on':
            self.sendCommand('OP' + str(channel) + ' 1\n')
        elif state == 'off':
            self.sendCommand('OP' + str(channel) + ' 0\n')
        else:
            pass
        
    def shutdown(self):
        self.close()
        
class XilabController():
    
    #http://files.xisupport.com/8SMC4-USB_Programming_manual_Eng.pdf
    
    device = None
    deviceID_1 = -1
    deviceID_2 = -1
    deviceID_3 = -1
    visaName = ""
    #def __init__(self, port, compliance, average = 1):
        #super(Keithley6517, self).__init__(port)t)

    def __init__(self):
        self.visaName = ""

    #def setup_dependencies(self):

            
    def setup_devices(self):
        
        #self.setup_dependencies()
        print("Library loaded")
        
        sbuf = create_string_buffer(64)
        lib.ximc_version(sbuf)
        
        print("Library version: " + sbuf.raw.decode().rstrip("\0"))
        
        result = lib.set_bindy_key(os.path.join(ximc_dir, "win32", "keyfile.sqlite").encode("utf-8"))
        if result != Result.Ok:
            lib.set_bindy_key("keyfile.sqlite".encode("utf-8")) # Search for the key file in the current directory.
        
        # This is device search and enumeration with probing. It gives more information about devices.
        probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
        enum_hints = b"addr="
        # enum_hints = b"addr=" # Use this hint string for broadcast enumerate
        devenum = lib.enumerate_devices(probe_flags, enum_hints)
        print("Device enum handle: " + repr(devenum))
        print("Device enum handle type: " + repr(type(devenum)))
        
        dev_count = lib.get_device_count(devenum)
        print("Device count: " + repr(dev_count))
        
        controller_name = controller_name_t()
        for dev_ind in range(0, dev_count):
            enum_name = lib.get_device_name(devenum, dev_ind)
            result = lib.get_enumerate_device_controller_name(devenum, dev_ind, byref(controller_name))
            if result == Result.Ok:
                print("Enumerated device #{} name (port name): ".format(dev_ind) + repr(enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")
        
        flag_virtual = 0
        
        # open_name = None
        # if len(sys.argv) > 1:
            # open_name = sys.argv[1]
        # elif dev_count > 0:
            # open_name = lib.get_device_name(devenum, 0)
        # elif sys.version_info >= (3,0):
            # # use URI for virtual device when there is new urllib python3 API
            # tempdir = tempfile.gettempdir() + "/testdevice.bin"
            # if os.altsep:
                # tempdir = tempdir.replace(os.sep, os.altsep)
            # # urlparse build wrong path if scheme is not file
            # uri = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme="file", \
                    # netloc=None, path=tempdir, params=None, query=None, fragment=None))
            # open_name = re.sub(r'^file', 'xi-emu', uri).encode()
            # flag_virtual = 1
            # print("The real controller is not found or busy with another app.")
            # print("The virtual controller is opened to check the operation of the library.")
            # print("If you want to open a real controller, connect it or close the application that uses it.")
        
        # if not open_name:
            # exit(1)
        
        # if type(open_name) is str:
            # open_name = open_name.encode()
        
        # print("\nOpen device " + repr(open_name))
        # device_id = lib.open_device(open_name)
        
        
        # print("Device id: " + repr(device_id))
        
        self.device = lib        
        self.deviceID_1 = lib.open_device(lib.get_device_name(devenum, 0))
        self.deviceID_2 = lib.open_device(lib.get_device_name(devenum, 1))
        self.deviceID_3 = lib.open_device(lib.get_device_name(devenum, 2))
        
        
        print ("Xilab Controller Setup Completed")
                
    def setup(self):
        #setup_dependencies()
        self.setup_devices()
                    
    def get_info(self, device_id, suppressPrint = True):
        print("\nGet device info")
        x_device_information = device_information_t()
        result = self.device.get_device_information(device_id, byref(x_device_information))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Device information:")
            print(" Manufacturer: " +
                    repr(string_at(x_device_information.Manufacturer).decode()))
            print(" ManufacturerId: " +
                    repr(string_at(x_device_information.ManufacturerId).decode()))
            print(" ProductDescription: " +
                    repr(string_at(x_device_information.ProductDescription).decode()))
            print(" Major: " + repr(x_device_information.Major))
            print(" Minor: " + repr(x_device_information.Minor))
            print(" Release: " + repr(x_device_information.Release))
    
    def get_status(self, device_id, suppressPrint = True):
        print("\nGet status")
        x_status = status_t()
        result = self.device.get_status(device_id, byref(x_status))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Status.Ipwr: " + repr(x_status.Ipwr))
            print("Status.Upwr: " + repr(x_status.Upwr))
            print("Status.Iusb: " + repr(x_status.Iusb))
            print("Status.Flags: " + repr(hex(x_status.Flags)))
    
    def get_position(self, device_id, suppressPrint = True):
        print("\nRead position")
        x_pos = get_position_t()
        result = self.device.get_position(device_id, byref(x_pos))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Position: {0} steps, {1} microsteps".format(x_pos.Position, x_pos.uPosition))
        return x_pos.Position, x_pos.uPosition
    
    def move_left(self, device_id, suppressPrint = True):
        if not suppressPrint: print("\nMoving left")
        result = self.device.command_left(device_id)
        if not suppressPrint: print("Result: " + repr(result))
    
    def move_to(self, device_id, distance, udistance, suppressPrint = True):
        if not suppressPrint: print("\nGoing to {0} steps, {1} microsteps".format(distance, udistance))
        result = self.device.command_move(device_id, distance, udistance)
        if not suppressPrint: print("Result: " + repr(result))  
    
    def wait_for_stop(self, device_id, interval, suppressPrint = True):
        if not suppressPrint: print("\nWaiting for stop")
        result = self.device.command_wait_for_stop(device_id, interval)
        if not suppressPrint: print("Result: " + repr(result))
    
    def read_serial(self, device_id, suppressPrint = True):
        print("\nReading serial")
        x_serial = c_uint()
        result = self.device.get_serial_number(device_id, byref(x_serial))
        if result == Result.Ok:
            print("Serial: " + repr(x_serial.value))
    
    def get_speed(self, device_id, suppressPrint = True)        :
        print("\nGet speed")
        # Create move settings structure
        mvst = move_settings_t()
        # Get current move settings from controller
        result = self.device.get_move_settings(device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        print("Read command result: " + repr(result))    
        
        return mvst.Speed
            
    def set_speed(self, device_id, speed, suppressPrint = True):
        if not suppressPrint: print("\nSet speed")
        # Create move settings structure
        mvst = move_settings_t()
        # Get current move settings from controller
        result = self.device.get_move_settings(device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        if not suppressPrint: print("Read command result: " + repr(result))
        if not suppressPrint: print("The speed was equal to {0}. We will change it to {1}".format(mvst.Speed, speed))
        # Change current speed
        mvst.Speed = int(speed)
        # Write new move settings to controller
        result = self.device.set_move_settings(device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        if not suppressPrint: print("Write command result: " + repr(result))    
        
    def set_zero_pos(self, device_id, suppressPrint = True):
        self.device.command_zero(device_id)
        #print("Write command result: " + repr(result))    
    
    def set_microstep_mode_256(self, device_id, suppressPrint = True):
        if not suppressPrint: print("\nSet microstep mode to 256")
        # Create engine settings structure
        eng = engine_settings_t()
        # Get current engine settings from controller
        result = self.device.get_engine_settings(device_id, byref(eng))
        # Print command return status. It will be 0 if all is OK
        if not suppressPrint: print("Read command result: " + repr(result))
        # Change MicrostepMode parameter to MICROSTEP_MODE_FRAC_256
        # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
        eng.MicrostepMode = MicrostepMode.MICROSTEP_MODE_FRAC_256
        # Write new engine settings to controller
        result = self.device.set_engine_settings(device_id, byref(eng))
        # Print command return status. It will be 0 if all is OK
        if not suppressPrint: print("Write command result: " + repr(result))  
       


    #New functions written by jm

    
    def calc_steps(self, distance, suppressPrint = True):
        #Given the distance (in um) calcualte the number of steps and micro steps needed.
        #Given a pre-measured calibration (fairly consistent)
        #Assuming 256 usteps in 1 step
        
        #In 100um, there are 40 steps and 16 micro steps
        steps_per_micron = 0.400625
        
        unsigned_distance = np.abs(distance)
        sign_distance = np.sign(distance)
        
        total_steps = unsigned_distance * steps_per_micron
        pure_steps = int(total_steps)
        decimal_steps = total_steps - pure_steps
        micro_steps = int(decimal_steps * 256)
        
        return int(pure_steps * sign_distance), int(micro_steps * sign_distance)
                
    def move_to_microns(self, device_id, distance, suppressPrint = True):
        steps, usteps = self.calc_steps(distance)
        self.move_to(device_id, steps, usteps)
        
    def return_home(self, device_id):
        steps, usteps = self.get_position(device_id, suppressPrint = True)
        #self.move(device_id, -steps, -usteps)
        self.move_to(device_id, 0, 0)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        