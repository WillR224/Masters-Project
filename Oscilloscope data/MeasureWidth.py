from __future__ import print_function
import sys, os, time, platform, csv
import os.path
from Devices import Keithley2410
from Devices import Keithley6487
from Devices import KeysightE4980AL
from Devices import Keithley6517
from Devices import Keithley6517_Serial
from Devices import AgilentMSO9254A
from Devices import MX180TP
from Devices import XilabController
from MeasurementFunctions import measureCV
from MeasurementFunctions import measureIV_PS
from MeasurementFunctions import measureIV_SMU
from MeasurementFunctions import measureCV_SMU
import TestFunctions as tests
from MeasurementFunctions import ERROR
from datetime import datetime
import colorama
import pyvisa as visa
import serial
from distutils.dir_util import copy_tree

colorama.init(autoreset=True) #used for colour printing    

try:
    import libximc.highlevel as ximc
    print("Use libximc {} that has been found among the pip installed packages".format(ximc.ximc_version()))
except ImportError:
    print("Warning! libximc cannot be found among the pip installed packages. Did you forget to install it via pip?\n"
          "Trying to import the library using relative path: ../../../ximc/crossplatform/wrappers/python ...")
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    ximc_dir = os.path.join(cur_dir, "ximc-2.14.27","ximc")
    ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python")
    print(ximc_package_dir)
    sys.path.append(ximc_package_dir)
    import libximc.highlevel as ximc
    print("Success!")

print("Library version: " + ximc.ximc_version())


def move(axis: ximc.Axis, distance: int, udistance: int) -> None:
    print("\nGoing to {0} steps, {1} microsteps".format(distance, udistance))
    axis.command_move(distance, udistance)

def status(axis: ximc.Axis) -> None:
    print("\nGet status")
    status = axis.get_status()
    print("Status.Ipwr: {}".format(status.Ipwr))
    print("Status.Upwr: {}".format(status.Upwr))
    print("Status.Iusb: {}".format(status.Iusb))
    print("Status.Flags: {}".format(status.Flags))

def takeData(fileName) -> None:
    oscVisaName = "USB0::0x2A8D::0x900E::MY53310147::INSTR"

    myOSC = AgilentMSO9254A(oscVisaName)
    try:
        myOSC.setup()
    except Exception as e:
        print (e)
        ERROR('OSC setup failed.')
        return 1
        
    #outputFolder = "C:\\Users\\Administrator\\Desktop\\Python Output Folder\\Tests"
    outputFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\TestWill\\"

    try:    
        #This is test function where we can check how to actually save
        fileName = outputFolder + "\\" + fileName;
        #myOSC.setChannelScale(1, 500E-3)
        myOSC.singleMeasurement();    
        print("fileName = " + str(fileName))
        time.sleep(0.5)
        myOSC.saveWaveformXY(fileName);                      
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

def initilise():
    enum_flags = ximc.EnumerateFlags.ENUMERATE_PROBE | ximc.EnumerateFlags.ENUMERATE_NETWORK

    enum_hints = "addr="
    devenum = ximc.enumerate_devices(enum_flags, enum_hints)
    print("Device count: {}".format(len(devenum)))
    print("Found devices:\n", devenum)

    flag_virtual = 0

    open_name = None
    if len(sys.argv) > 1:
        open_name = sys.argv[1]
        print("open_name = ", open_name)
    elif len(devenum) > 0:
        open_name = devenum[0]["uri"]
        print("open_name = ", open_name)
    else:
        tempdir = os.path.join(os.path.expanduser('~'), "testdevice.bin")
        open_name = "xi-emu:///" + tempdir
        flag_virtual = 1
        print("The real controller is not found or busy with another app.")
        print("The virtual controller is opened to check the operation of the library.")
        print("If you want to open a real controller, connect it or close the application that uses it.")
        print("open_name = ", open_name)
    return open_name


dist = 0
def run(direction,step):

    if direction == "x":
        open_name = initialise()
    elif direction == "y":
        open_name = initilise()
    else:
        print("axis not found")

    axis = ximc.Axis(open_name)
    axis.open_device()
    
    while dist < 1000:
        for i in range(3):
            fileName = direction + "BeamSize_" + str(dist) + "_" + str(i)
            takeData(fileName)
        move(axis,step,0)
        dist += step


run("x",30)

print('')
print('Test finished - shutting down instruments.')
print("")
print("")
print("")

colorama.deinit()


