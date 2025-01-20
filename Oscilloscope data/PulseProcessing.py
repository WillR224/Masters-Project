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
fig2 = plt.figure(dpi=130)

def getData(fileName):
    Dir = r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Oscilloscope data\\First ETCT width scans\\New folder\\'
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
    ax2.plot([cutP,cutP],[-1,1e-1],label = "Cut")
    ax2.plot([cutP-8e-9,cutP-8e-9],[-1,1e-1])
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
    ax3.plot([cutP,cutP],[-7e-9,5e-10],label = "cut")
    ax3.plot([cutP-8e-9,cutP-8e-9],[-7e-9,5e-10],label = "cut")
    ax3.set_xlabel("time (s)")
    ax3.set_ylabel("Integral of V(t)")
    ax3.set_title("Integral of LGAD pulse vs time with cut")


def integrate(x,y):
    I = scpI.cumtrapz(y,x, initial = 0)
    return x,I

def cut(x,y):
    peak = []
    for k in range(len(x)):
        if x[k]>(cutP-8e-9) and x[k]<cutP:
            peak.append([x[k],y[k]])
    peakArr = np.array(peak)
    return peakArr

def sample(x,y):
    data = []
    for k in range(len(x)):
        if x[k]>(-2e-8) and x[k]<(-1.2e-8):
            data.append([x[k],y[k]])
    dataArr = np.array(data)
    return dataArr

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


def chisquare(vals,fitvals,errors):
    return np.abs(np.sum(((vals-fitvals)/errors)**2))


def sCurveSingle(fileNameArray,direction):
    integrals = []
    noise = []
    for i in range(len(fileNameArray)):
        data = getData(fileNameArray[i])
        cutArr = cut(data[:,0],data[:,2])
        noiseSample = sample(data[:,0],data[:,2])
        xI, I = integrate(cutArr[:,0],cutArr[:,1])
        Integral = np.min(I)
        integrals.append(Integral)
        xR, R = integrate(noiseSample[:,0],noiseSample[:,1])
        noise.append(np.max(np.abs(R)))

    print(steps)
    Rvals = np.array([steps[0:len(fileNameArray)],integrals[0:len(fileNameArray)]])

    plt.title(f"Plot of integrated current vs distance scan in the depth direction (fine)")
    plt.xlabel("Scan distance ($\mu$m)")
    plt.ylabel("Integrated current $\propto$ charge collected (C)")
    plt.plot(steps,integrals, label = f"{direction}-Integral data", marker  = "x", linestyle = "")
    plt.errorbar(steps,integrals,noise, marker = None, linestyle = "", color = "#1f77b4")
    Rpopt, Rpcov , Rextras1, Rextras2, Rextras3 = curve_fit(erf, Rvals[0], Rvals[1], [-4e-10,0.1,-13,-5e-10], sigma = noise, full_output = True)
    Rarray = np.array([Rvals[0], Rpopt[0]*scpS.erf(Rpopt[1]*(Rvals[0]+Rpopt[2]))+Rpopt[3]])

    Rmean, Rstd = params(Rpopt[1],Rpopt[2])
    Rmeanerr, Rstderr = errorsmean(Rpcov), errorssig(Rpcov,Rpopt[2])
    print(Rmeanerr, Rstderr)
    chisquareR = np.sum(Rextras1["fvec"]**2)
    plt.plot(Rarray[0],Rarray[1],label = f"Best fit for Data: \n  $\sigma_x$ = {round(Rstd,4)}$\pm${np.abs(round(Rstderr,4))}$\mu$m \n $\chi^2$ per dof = {round(chisquareR/(len(fileNameArray)-1),4)}")

    print(*Rpopt)
    plt.legend(loc = 1, bbox_to_anchor=(1, 0.9), fontsize = 8)



#[4.5e-10,0.14,-100,-5e-10]

def sCurveDual(fileNameArray,direction):
    integrals = []
    noise = []
    for i in range(len(fileNameArray)):
        data = getData(fileNameArray[i])
        cutArr = cut(data[:,0],data[:,2])
        xI, I = integrate(cutArr[:,0],cutArr[:,1])
        print(xI,I)
        noiseSample = sample(data[:,0],data[:,2])
        Integral = np.min(I)
        integrals.append(Integral)
        xR, R = integrate(noiseSample[:,0],noiseSample[:,1])
        noise.append(np.max(np.abs(R)))

    print(steps)
    print(integrals)
    Rvals = np.array([steps[7:len(fileNameArray)],integrals[7:len(fileNameArray)]])
    Lvals = np.array([steps[0:9],integrals[0:9]])

    plt.title(f"Plot of integrated current vs distance scan in the depth direction")
    plt.xlabel("Scan distance ($\mu$m)")
    plt.ylabel("Integrated current $\propto$ charge collected (C)")
    plt.plot(steps,integrals, label = f"{direction}-Data", marker  = "x", linestyle = "")

    Rpopt, Rpcov , Rextras1, Rextras2, Rextras3 = curve_fit(erf, Rvals[0], Rvals[1], [4.5e-10,0.14,-180,-5e-10], sigma = noise[7:len(fileNameArray)], full_output = True)
    Lpopt, Lpcov, Lextras1, Lextras2, Lextras3 = curve_fit(erf, Lvals[0], Lvals[1], [-4e-10,0.14,-125,-4.7e-10], sigma = noise[0:9],full_output = True)

    Rarray = np.array([Rvals[0], Rpopt[0]*scpS.erf(Rpopt[1]*(Rvals[0]+Rpopt[2]))+Rpopt[3]])
    Larray = np.array([Lvals[0], Lpopt[0]*scpS.erf(Lpopt[1]*(Lvals[0]+Lpopt[2]))+Lpopt[3]])

    Rmean, Rstd = params(Rpopt[1],Rpopt[2])
    Lmean, Lstd = params(Lpopt[1],Lpopt[2])

    Rmeanerr, Rstderr, Lmeanerr, Lstderr = errorsmean(Rpcov), errorssig(Rpcov,Rpopt[2]), errorsmean(Lpcov), errorssig(Lpcov,Lpopt[2])
    Rmeanerr, Rstderr = errorsmean(Rpcov), errorssig(Rpcov,Rpopt[2])
    print(Rmeanerr, Rstderr, Lmeanerr, Lstderr)

    chisquareR = np.sum(Rextras1["fvec"]**2)
    chisquareL = np.sum(Lextras1["fvec"]**2)
    print(chisquareR,chisquareL)

    plt.plot(Rarray[0],Rarray[1],label = f"Best fit for Data: \n  $\sigma_x$ = {round(Rstd,4)}$\pm${np.abs(round(Rstderr,5))}$\mu$m \n $\chi^2$ per dof = {round(chisquareR/(len(Rarray[0])-1),4)}")
    plt.plot(Larray[0],Larray[1],label = f"Best fit for LHS: \n  $\sigma_y$ = {round(Lstd,4)}$\pm${np.abs(round(Lstderr,5))}$\mu$m \n $\chi^2$ per dof = {round(chisquareL/(len(Larray[0])-1),4)}")

    plt.errorbar(steps[6:len(fileNameArray)],integrals[6:len(fileNameArray)],noise[6:len(fileNameArray)], marker = None, linestyle = "", color = "#1f77b4")
    plt.errorbar(steps[0:8],integrals[0:8], noise[0:8], marker = None, linestyle = "", color = "#1f77b4")
    print(*Lpopt,*Rpopt)

    plt.legend(loc = 1, bbox_to_anchor=(1, 0.5), fontsize = 8)






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
    

#cutP = 3.1e-8
cutP = 2.2e-8

fileNameArrayY = []
j=-2990
while j < -2349:
    num = str(j)
    fileNameArrayY.append("EdgeTCTSizeScan+veYDirection\\50VBeamSizeEdgeY"+num+"X16805")
    j += 40
print(fileNameArrayY)

# fileNameArrayX = ["EdgeTCTSizeScan-veXDirectionOffset\\50VBeamSizeEdgeY-2700X16770"]
# j=16780
# steps = [0]
# while j < 16834:
#     num = str(j)
#     fileName = "EdgeTCTSizeScan-veXDirectionOffset\\50VBeamSizeEdgeY-2700X"+num
#     fileNameArrayX.append(fileName)
#     steps.append(2.5*(j-16770))
#     # fig1 = plt.figure(dpi=130)
#     # fig1.set_size_inches(8,5)
#     # plt.subplots_adjust(hspace = 0.6, wspace = 0.4)
#     # plot(fileName)
#     j += 5
# j = 16840
# while j < 16851:
#     num = str(j)
#     fileName = "EdgeTCTSizeScan-veXDirectionOffset\\50VBeamSizeEdgeY-2700X"+num
#     fileNameArrayX.append(fileName)
#     steps.append(2.5*(j-16770))
#     # fig1 = plt.figure(dpi=130)
#     # fig1.set_size_inches(8,5)
#     # plt.subplots_adjust(hspace = 0.6, wspace = 0.4)
#     # plot(fileName)
#     j += 5


fileNameArrayX = []
j=16800
steps = []
while j < 16871:
    num = str(j)
    fileName = "EdgeTCTSizeScanposXDirection/50VBeamSizeEdgeY-2700X"+num
    fileNameArrayX.append(fileName)
    steps.append(2.5*(j-16775))
    # fig1 = plt.figure(dpi=130)
    # fig1.set_size_inches(8,5)
    # plt.subplots_adjust(hspace = 0.6, wspace = 0.4)
    # plot(fileName)
    j += 5



print(fileNameArrayX)
file = "EdgeTCTSizeScan-veXDirectionOffset\\50VBeamSizeEdgeY-2700X16835"
#plot(file)
sCurveDual(fileNameArrayX,"X")
#sCurveSingle(fileNameArrayX,"X")
#sCurve(fileNameArrayY, "Y")

plt.show()