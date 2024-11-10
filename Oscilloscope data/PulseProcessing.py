# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 14:34:23 2024

@author: willr
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.integrate as scpI
# fig1 = plt.figure(dpi=500)
# fig1.set_size_inches(6, 9)
# ax = fig1.add_subplot()
# plt.ylabel('Voltage')
# plt.xlabel('Time')

def getData(fileName):
    Dir = r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Oscilloscope data\\First LGAD pulses 8-11 (50Hz,5%,-190V)\\'
    reader = pd.read_csv(Dir + fileName + '.csv', skiprows=24)
    data = reader.to_numpy()
    data_array = np.array(data)
    return data_array

def plot(fileName):
    data = getData(fileName)
    print(data[:,0],data[:,1])
    plt.plot(data[:,0],data[:,1])
    plt.plot(data[:,0],data[:,2])
    plt.plot(data[:,0],data[:,3])
    plt.show()

def differentiate(fileName):
    data = getData(fileName)
    d = np.gradient(data[:,1], data[:,0])
    plt.plot(d)
    plt.show()

def integrate(fileName):
    data = getData(fileName)
    I = scpI.cumtrapz(data[:,2],data[:,0], initial = 0)
    plt.plot(data[:,0],I)
    plt.show()
    
integrate("Test1")
plot("Test1")

