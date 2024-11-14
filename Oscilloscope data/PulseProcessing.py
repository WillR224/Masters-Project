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
import scipy.special as scpS
from scipy.optimize import curve_fit
fig1 = plt.figure(dpi=130)
fig1.set_size_inches(8,5)
plt.subplots_adjust(hspace = 0.6, wspace = 0.4)

def getData(fileName):
    Dir = r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Oscilloscope data\\LGAD beam measurements\\'
    #Dir = r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Oscilloscope data\\'
    reader = pd.read_csv(Dir + fileName + ".csv", skiprows=24)
    data = reader.to_numpy()
    data_array = np.array(data)
    return data_array

def plot(fileName):
    data = getData(fileName)
    ax = fig1.add_subplot(221)
    ax.plot(data[:,0],data[:,1])
    ax.plot(data[:,0],data[:,2])
    ax.plot(data[:,0],data[:,3])
    ax.set_ylabel("Voltage V(t)")
    ax.set_xlabel("time (s)")

    ax2 = fig1.add_subplot(222)
    ax2.plot([2.3e-8,2.3e-8],[-1,1e-1])
    ax2.plot(data[:,0],data[:,2])
    ax2.set_ylabel("Voltage V(t)")
    ax2.set_xlabel("time (s)")

    derivative_plot(data[:,0],data[:,2])
    integral_plot(data[:,0],data[:,2])
    #cut_and_integrate(fileName)
    cutArr = cut(data[:,0],data[:,2])
    print(cutArr)
    fig2 = plt.figure(dpi=100)
    Ix,Iy = integrate(cutArr[:,0],cutArr[:,1])
    print(Ix,Iy)
    plt.plot(Ix,Iy)

def derivative_plot(x,y):
    ax4 = fig1.add_subplot(224)
    d = differentiate(x,y)[1]
    ax4.plot(x,d)
    ax4.set_xlabel("time (s)")
    ax4.set_ylabel("Derivative of V(t)")
    ax4.set_title("Derivatie of LGAD pulse vs time")

def differentiate(x,y):
    d = np.gradient(y,x)
    return (x,d)
    
def integral_plot(x,y):
    ax3 = fig1.add_subplot(223)
    I = integrate(x,y)[1]
    ax3.plot(x,I)
    ax3.plot([2.3e-8,2.3e-8],[-7e-9,5e-10])
    ax3.set_xlabel("time (s)")
    ax3.set_ylabel("Integral of V(t)")

def integrate(x,y):
    I = scpI.cumtrapz(y,x, initial = 0)
    return(x,I)

def cut(x,y):
    peak = []
    for k in range(len(x)):
        if x[k]>0 and x[k]<2.3e-8:
            peak.append([x[k],y[k]])
    peakArr = np.array(peak)
    return peakArr

def integ(fileName):
    data = getData(fileName)
    Integral = scpI.cumtrapz(data[:,2],data[:,0], initial = 0)
    I = np.array([data[:,0],Integral])
    peak = []
    peakInt = np.min(peakArr[:,1])
    return peakInt

def sCurve(fileNameArray,method):
    integs = []
    for i in fileNameArray:
        int = integ(i)
        integs.append(int)
    steps = np.linspace(0,870,30)
    plt.plot(steps,integs)
    Rvals = np.array([steps[11:30],integs[11:30]])
    Lvals = np.array([steps[0:15],integs[0:15]])
    if method == 0:
        Rpopt, Rpcov = curve_fit(erf, Rvals[0],Rvals[1], [1e-9,0,0,0])
        Lpopt,Lpcov = curve_fit(erf, Lvals[0], Lvals[1], [1e-9,0,0,0])
        Rarray = np.array([Rvals[0], Rpopt[0]*scpS.erf(Rpopt[1]*Rvals[0]+Rpopt[2])+Rpopt[3]])
        Larray = np.array([Lvals[0], Lpopt[0]*scpS.erf(Lpopt[1]*Lvals[0]+Lpopt[2])+Lpopt[3]])
        plt.plot(Rarray[0],Rarray[1])
        plt.plot(Larray[0],Larray[1])
        fig2 = plt.figure(dpi=130)
        plt.plot(Rarray[0], np.gradient(Rarray[1],Rarray[0]))
        plt.plot(Larray[0], np.gradient(Larray[1],Larray[0]))

    elif method == 1:
        Rdiv = np.gradient(Rvals[1],Rvals[0])
        Ldiv = np.gradient(Lvals[1],Lvals[0])
        Rpopt, Rpcov = curve_fit(gauss, Rvals[0],Rvals[1], [400,600,1e-11,100])
        Lpopt,Lpcov = curve_fit(gauss, Lvals[0], Lvals[1], [50,200,1e-11,100])
        Rarray = np.array([Rvals[0], gauss(Rvals[0],Rpopt[0],Rpopt[1],Rpopt[2],Rpopt[3])])
        Larray = np.array([Lvals[0], gauss(Lvals[0],Lpopt[0],Lpopt[1],Lpopt[2],Lpopt[3])])
        fig2 = plt.figure(dpi=130)
        plt.plot(Rvals[0],Rdiv)
        plt.plot(Lvals[0],Ldiv)
        #plt.plot(Rarray[0],Rarray[1])
        #plt.plot(Larray[0],Larray[1])

    elif method == 2:
        Rdiv = np.gradient(Rvals[1],Rvals[0])
        Ldiv = np.gradient(Lvals[1],Lvals[0])
        Rpopt, Rpcov = curve_fit(gauss1, Rvals[0],Rvals[1], [50,60,5e-11], bounds = ((25,500,1e-12), (75,700,1e-10)))
        Lpopt,Lpcov = curve_fit(gauss1, Lvals[0], Lvals[1], [50,-200,5e-11], bounds = ((25,-300,1e-12), (75,-100,1e-10)))
        Rarray = np.array([Rvals[0], gauss1(Rvals[0],Rpopt[0],Rpopt[1],Rpopt[2])])
        Larray = np.array([Lvals[0], gauss1(Lvals[0],Lpopt[0],Lpopt[1],Lpopt[2])])
        fig2 = plt.figure(dpi=130)
        plt.plot(Rvals[0],Rdiv)
        plt.plot(Lvals[0],Ldiv)
        plt.plot(Rarray[0],Rarray[1])
        plt.plot(Larray[0],Larray[1])
        print(Rvals[0])

    else:
        return "fn not found"
    

def erf(z,a,b,c,d):
   return a*scpS.erf(b*z+c)+d

def gauss(z,a,b,c,d):
    return c*(1/np.sqrt(2*np.pi)*a)*np.exp((-1/2)*((z-b)/a)**2)+d

def gauss1(z,a,b,c):
    return (c/(np.sqrt(2*np.pi)))*np.exp((-1/2)*((z-b)/a)**2)

fileNameArray = []
j=0
while j < 30:
    j += 1
    num = str(j)
    fileNameArray.append("BeamSizeX"+num)

file = "BeamSizeX12"
#plot(file)
#sCurve(fileNameArray,1)
plt.suptitle("Plots for the X direction of the beam")

plot(file)
plt.show()
