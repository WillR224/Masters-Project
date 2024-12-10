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
    ax.plot(data[:,0],data[:,1],label = "Laser trigger", color = "C1")
    ax.plot(data[:,0],data[:,2],label = "Sensor Pulse", color = "C0")
    ax.plot(data[:,0],data[:,3], label = "Beam monitor", color = "C2")
    ax.set_ylabel("Voltage V(t)")
    ax.set_xlabel("time (s)")
    ax.set_title("LGAD pulse, laser trigger & beam monitor.")
    ax.legend(fontsize = 8)

    ax2 = fig1.add_subplot(222)
    ax2.plot(data[:,0],data[:,2],label = "Sensor Pulse")
    ax2.plot([2.3e-8,2.3e-8],[-1,1e-1],label = "Cut")
    ax2.set_ylabel("Voltage V(t)")
    ax2.set_xlabel("time (s)")
    ax2.set_title("LGAD pulse vs time with cut")

    derivative_plot(data[:,0],data[:,2])
    integral_plot(data[:,0],data[:,2])


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
    ax3.plot(x,integrate(x,y)[1],label = "Integrated Pulse")
    ax3.plot([2.3e-8,2.3e-8],[-7e-9,5e-10],label = "cut")
    ax3.set_xlabel("time (s)")
    ax3.set_ylabel("Integral of V(t)")
    ax3.set_title("Integral of LGAD pulse vs time with cut")


def integrate(x,y):
    I = scpI.cumtrapz(y,x, initial = 0)
    return x,I

def cut(x,y):
    peak = []
    for k in range(len(x)):
        if x[k]>0 and x[k]<2.3e-8:
            peak.append([x[k],y[k]])
    peakArr = np.array(peak)
    return peakArr

#def integ(fileName):
#     data = getData(fileName)
#    Integral = scpI.cumtrapz(data[:,2],data[:,0], initial = 0)
#    I = np.array([data[:,0],Integral])
#    peak = []
#    peakInt = np.min(peakArr[:,1])
#    return peakInt

def params(b,c):
    std = 1/(np.sqrt(2)*b)
    mean = (-1)*c
    return mean, std

def errors1(cov_matrix,a,b,c,mean):
    z = mean
    dfa = scpS.erf(b*(c+z))
    dfb = (2*a/np.sqrt(np.pi))*(c+z)*np.exp(-(b**2)*(c+z)**2)
    dfc = (2*a*b/np.sqrt(np.pi))*np.exp(-(b**2)*(c+z)**2)
    dfd = 1

    derivatives = np.array([dfa,dfb,dfc,dfd])
    multi = np.matmul(derivatives, cov_matrix)
    error = np.matmul(multi, derivatives.T)
    return np.sqrt(error)

def errorsmean(cov_matrix):
    return np.sqrt(cov_matrix[2][2])

def errorssig(cov_matrix,b):
    varb = cov_matrix[1][1]
    sigerror = np.sqrt(varb)*(1/b)*2**(-1/4)
    return sigerror

def sCurve(fileNameArray,direction):
    integrals = []
    for i in range(len(fileNameArray)):
        data = getData(fileNameArray[i])
        cutArr = cut(data[:,0],data[:,2])
        xI, I = integrate(cutArr[:,0],cutArr[:,1])
        Integral = np.min(I)
        integrals.append(Integral)

    steps = np.arange(2.5*8,2.5*1158,2.5*50)
    Rvals = np.array([steps[10:25],integrals[10:25]])
    Lvals = np.array([steps[0:12],integrals[0:12]])
    fig2 = plt.figure(dpi=130)
    plt.title(f"Plot of integrated current vs distance scan the {direction} direction")
    plt.xlabel("Scan distance ($\mu$m)")
    plt.ylabel("Integrated current $\propto$ charge collected (C)")
    plt.plot(steps,integrals, label = "Data", marker  = "x")

    Rpopt, Rpcov = curve_fit(erf, Rvals[0], Rvals[1], [5e-10,0.004,-1900,-5e-10])
    Lpopt,Lpcov = curve_fit(erf, Lvals[0], Lvals[1], [-5e-10,0.004,-900,-5e-10])
    Rarray = np.array([Rvals[0], Rpopt[0]*scpS.erf(Rpopt[1]*(Rvals[0]+Rpopt[2]))+Rpopt[3]])
    Larray = np.array([Lvals[0], Lpopt[0]*scpS.erf(Lpopt[1]*(Lvals[0]+Lpopt[2]))+Lpopt[3]])
    Rmean, Rstd = params(Rpopt[1],Rpopt[2])
    Lmean, Lstd = params(Lpopt[1],Lpopt[2])
    Rmeanerr, Rstderr, Lmeanerr, Lstderr = errorsmean(Rpcov), errorssig(Rpcov,Rpopt[2]), errorsmean(Lpcov), errorssig(Lpcov,Lpopt[2])
    plt.plot(Rarray[0],Rarray[1],label = f"Best fit for RHS: \n $\mu$ = {round(Rmean)}$\pm${round(Rmeanerr)}$\mu$m \n $\sigma$ = {round(Rstd)}$\mu$m")
    plt.plot(Larray[0],Larray[1],label = f"Best fit for LHS: \n $\mu$ = {round(Lmean)}$\pm${round(Lmeanerr)}$\mu$m \n $\sigma$ = {round(Lstd)}$\mu$m")
    print(*Lpopt,*Rpopt)
    #plt.plot(Rarray[0],Rarray[1])
    #plt.plot(Larray[0],Larray[1])
    plt.legend(loc = 1, bbox_to_anchor=(1, 0.42), fontsize = 10)


def erf(z,a,b,c,d):
   return a*scpS.erf(b*(z+c))+d

def dualPlot(fileName1,fileName2):
    data1 = getData(fileName1)
    data2 = getData(fileName2)
    ax = fig1.add_subplot(xlim = (-30,70))
    cutArr1 = cut(data1[:,0],data1[:,2])
    xI1, I1 = integrate(cutArr1[:,0],cutArr1[:,1])
    integral1 = np.min(I1)
    cutArr2 = cut(data2[:,0],data2[:,2])
    xI2, I2 = integrate(cutArr2[:,0],cutArr2[:,1])
    integral2 = np.min(I2)
    ax.plot(data1[:,0]*(1e9),data1[:,2],label = f"LGAD Pulse, I = {integral1:.2e}", color = "r")
    ax.plot(data2[:,0]*(1e9),data2[:,2],label = f"PiN Pulse, I = {integral2:.2e}", color = "b")
    ax.set_ylabel("Voltage (V)")
    ax.set_xlabel("time (ns)")
    ax.set_title("LGAD pulse & PiN pulse")
    ax.legend(fontsize = 10)
    

fileNameArray = []
j=1
while j < 31:
    num = str(j)
    fileNameArray.append("BeamSizeY"+num)
    j += 1

file = "BeamSize_281124_PIN\\BeamSizeX26296"
sCurve(fileNameArray,"y")
#plt.suptitle("Plots for the X direction of the beam")
plot(file)
#plot("LGAD beam measurements\\BeamSizeY14")
#dualPlot("LGAD beam measurements\\BeamSizeY14",file)

plt.show()