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


XlC = XilabController()


try:
    XlC.setup()
except Exception as e:
    print (e)
    return 1

#print("XlC.deviceID_1 = " + str(XlC.deviceID_1))

print('')
print('Initialising Stage')  

print('')
#print('Setting micro step mode (256)')
XlC.set_microstep_mode_256(XlC.deviceID_1)
XlC.set_microstep_mode_256(XlC.deviceID_2)
XlC.set_microstep_mode_256(XlC.deviceID_3)        


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

Location = "C:\\Users\\bilpa_login\\Desktop\\"
outputFolder = "\\\\EPLDT092\\LGAD_Project\\Oscilloscope_Data\\TestWill\\"


def jmFineSearch1D(XlC, myOSC, outputFolder, device_ID, dist, scanStep):
    '''
    Code adapted from Jonathan Mulvey scripts 
    '''
    scanDistance = 500 
    scanStep = 20 

    end = dist/2.5
    pos = 0
    while pos < end:
        pos = pos + scanStep
    
        XlC.move_to_microns(device_ID, pos)                       
        XlC.wait_for_stop(device_ID, 100)
           
        myOSC.singleMeasurement()
        time.sleep(0.2)                         
        
        fileName = outputFolder+dist
        print("fileName = " + str(fileName))
        myOSC.saveWaveformXY(fileName)
        
        time.sleep(1)                      



jmFineSearch1D(XlC, myOSC, linkedFolder, save_folder, scan_folder, scan_filename, XlC.deviceID_2)