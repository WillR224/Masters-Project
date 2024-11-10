#!/usr/bin/python
# Interfaces.py -- contains class wrappers for interfacing with sockets, serial ports, and GPIB connections
# Updated: 01/03/2021
# Contributing: Matt Basso (University of Toronto), Will George (University of Birmingham)

import time, serial, socket, sys
try:
    import pyvisa
    import visa
except ImportError:
    print('ERROR :: please ensure NIVISA and PyVISA are installed!')
    print('--> See: https://pyvisa.readthedocs.io/en/1.8/getting_nivisa.html#getting-nivisa')
    print('--> See: https://pyvisa.readthedocs.io/en/1.8/getting.html')
    sys.exit(1)

class Serial(object):
    __slots__ = ['port','serial']

    def __init__(self,port = None):
        super(Serial,self).__init__()
        self.port = port
        self.serial = None

    def open(self,port = None):
        if port is not None:
            self.port = port
        self.serial = serial.Serial(port = self.port,baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS,timeout = 2)
        self.serial.flush()

    def close(self):
        self.serial.close()

    def sendCommand(self,command,wait_for = 0.1):
        self.serial.write((command + '\n').encode())
        time.sleep(wait_for)

    def getData(self):
        data = self.serial.readline().strip()
        data_str = data.decode()
        return data_str


class Socket(object):

    __slots__ = ['ip','port','socket']

    def __init__(self, ip = None, port = None):
        super(Socket, self).__init__()
        self.ip     = ip
        self.port   = port
        self.socket = None


    def open(self, ip = None, port = None):
        if ip is not None:
            self.ip = ip
        if port is not None:
            self.port = port
        self.socket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        self.socket.settimeout(10)
        self.socket.connect((self.ip, self.port))
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def close(self):
        self.socket.close()

    def sendCommand(self,command,wait_for = 0.1):
        self.socket.send((command + '\n').encode())
        time.sleep(wait_for)

    def getData(self):
        data = self.socket.recv(1024).strip()
        data_str = data.decode()
        return data_str


class GPIB(object):

    __slots__ = ['device_id', 'rm', 'response']

    def __init__(self, device_id = None):
        super(GPIB, self).__init__()
        self.device_id = device_id
        self.rm        = None
        self.response  = None

    def open(self, device_id = None):
        if device_id is not None:
            self.device_id = device_id
        # See: https://stackoverflow.com/questions/51520737/pyvisa-attributeerror-nivisalibrary-object-has-no-attribute-viparsersrcex
        self.rm = pyvisa.ResourceManager().open_resource(self.device_id)

    def close(self):
        self.rm.close()
        self.rm = None

    def sendCommand(self, command, wait_for = 5, converter = 's'): #wait_for = 0.1
        # See: https://docs.python.org/2/library/string.html#formatspec
        self.response = self.rm.query_ascii_values(command + '\n', converter = converter)
        time.sleep(wait_for)
        # We close and re-open the resource manager to allow us to send more commands (hacky?)
        # --> TODO: fix this!
        self.rm.close()
        self.rm.open()

    def sendCommandWriteOnly(self,command):
        self.rm.write(command)
        self.rm.close()
        self.rm.open()

    def sendCommandWriteRead(self,command):
        self.rm.write(command)
        self.response = self.rm.read()
        self.rm.close()
        self.rm.open()

    def sendCommandWithWait(self, command):
        self.rm.timeout = 60000
        self.rm.write(command + '\n')
        response = self.rm.read('\n')
        self.rm.timeout = 5000
        self.rm.close()
        self.rm.open()
        return response

    def getData(self):
        return self.response
