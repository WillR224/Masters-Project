import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.special as scpS
from scipy.optimize import curve_fit
from astropy.io import fits
from matplotlib import cm
from matplotlib.ticker import LinearLocator

hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\2024-11-15_11_40_24Z\\2024-11-15-1140_4-CapObj_0000.FIT')
###############################
###                         ###
###  3D Plotting & Fitting  ###
###                         ###
###############################
def threeD():
    def func(data,I_0,a,L,c,d):
        s = np.sqrt(((2*np.array(data[0])-c))**2+((2*np.array(data[1])-d))**2)/L
        w = ((2*np.pi*a)/(1.06))*s
        j1 = scpS.jv(1,w)
        return I_0*((2*j1/w)**2)

    X = np.arange(1100, 1200, 1)
    Y = np.arange(1450, 1500, 1)
    Xmesh, Ymesh = np.meshgrid(X, Y)
    Z = np.array(hdul1[0].data[1450:1500,1100:1200])

    dataPoints = []
    for i in X:
        for j in Y:
            dataPoints.append([i,j,hdul1[0].data[j,i]])        
    arrayDataPoints = np.array(dataPoints)

    # popt,pcov = curve_fit(func,(arrayDataPoints[:,0],arrayDataPoints[:,1]),arrayDataPoints[:,2],[70000,3000,80000,2300,2950], bounds = ([60000,2000,70000,2250,2900],[90000,4000,120000,2350,3000]))
    # print(*popt)
    # modelZData = func((arrayDataPoints[:,0],arrayDataPoints[:,1]), *popt)
    # modelZDataReshape = np.reshape(modelZData,(50,100),order = "F")
    # fig3 = plt.figure()
    # plt.pcolor(Xmesh,Ymesh,modelZDataReshape, shading = "auto", cmap=cm.coolwarm)
    # plt.colorbar()

    # fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    # surf = ax.plot_surface(Xmesh, Ymesh, modelZDataReshape, cmap=cm.coolwarm, linewidth=0)

    fig4, ax4 = plt.subplots(subplot_kw={"projection": "3d"})
    surf = ax4.plot_surface(Xmesh, Ymesh, Z, cmap=cm.coolwarm, linewidth=0)

    fig2 = plt.figure()
    plt.pcolor(Xmesh, Ymesh, Z, vmin=np.min(Z) * 2, cmap=cm.coolwarm)
    plt.colorbar()
    plt.show()

###############################
###                         ###
###  2D Plotting & Fitting  ###
###                         ###
###############################
def twoD(slice,direction,range,guesses,Lbounds,Ubounds):
    def single(x,I_0,a,b,L):
        theta = np.arctan((2*np.array(x)-b)/L)
        beta = np.pi*a*np.sin(theta)/1.06
        return I_0*((np.sin(beta))/beta)**2

    def double(x,I_0,a,b,L,c):
        theta = np.arctan((2*np.array(x)-b)/L)
        beta = np.pi*a*np.sin(theta)/1.06
        gamma = np.pi*c*np.sin(theta)/1.06
        return I_0*(((np.sin(beta))/beta)**2)*(np.cos(gamma))**2
    
    X = np.arange(*range, 1)
    if direction == "x":
        Z = np.array(hdul1[0].data[slice,range[0]:range[1]])
    elif direction == "y":
        Z = np.array(hdul1[0].data[range[0]:range[1],slice])
    else:
        print("Direction not found")
    Z = np.array(hdul1[0].data[1450:1500,1100:1200])
    print(Z)
    Xhires = np.arange(*range, 0.1)
    poptd, pcovd = curve_fit(double, X, Z, guesses, bounds = (Lbounds,Ubounds))
    popts, pcovs = curve_fit(single, X, Z, [*guesses[0:4]], bounds = ([*Lbounds[0:4]],[*Ubounds[0:4]]))
    fig1 = plt.figure(dpi = 100)
    plt.plot(X,Z)
    plt.plot(Xhires,double(Xhires,*poptd),label = f"Parameters: I_0 = {round(poptd[0])} \n Slit Width = {round(poptd[1])} \n Slit-Screen Distance = {round(poptd[3])} \n Slit Separation = {round(poptd[4])}")
    plt.title(f"Data and Fit using 1D Double slit diffraction in the {direction} direction.")
    plt.xlabel("Pixel bin")
    plt.ylabel("Intensity")
    plt.legend(loc = 1, bbox_to_anchor=(1, 1), fontsize = 9)
    fig2 = plt.figure(dpi = 100)
    plt.plot(X,Z)
    plt.plot(Xhires,single(Xhires, *popts),label = f"Parameters: I_0 = {round(popts[0])} \n Slit Width = {round(popts[1])} \n Slit-Screen Distance = {round(popts[3])}")
    plt.title(f"Data and Fit using 1D single slit diffraction in the {direction} direction.")
    plt.xlabel("Pixel bin")
    plt.ylabel("Intensity")
    plt.legend(loc = 1, bbox_to_anchor=(1, 1), fontsize = 9)
    plt.show()

#twoD(1477,"x",[1100, 1200],[60000,3000,1,1,1],[0,0,0,0,0],[100000,6000,4000,120000,30000])
twoD(1477,"x",[1100, 1200],[60000.0,3000.0,2300.0,90000.0,10000.0],[40000.0,2000.0,2200.0,60000.0,1000.0],[80000.0,4000.0,2400.0,120000.0,30000.0])
#twoD(1148,"y",[1450, 1500],[60000,3000,2954,80000,10000],[40000,1000,2900,50000,0],[80000,6000,3000,120000,20000])

#threeD()