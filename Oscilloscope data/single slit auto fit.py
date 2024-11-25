import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.special as scpS
from scipy.optimize import curve_fit
from astropy.io import fits
from matplotlib import cm
from matplotlib.ticker import LinearLocator
import math

#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_03_45Z\\2024-11-21-1303_7-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_08_02Z\\2024-11-21-1308_0-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_10_02Z\\2024-11-21-1310_0-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_11_22Z\\2024-11-21-1311_3-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_12_24Z\\2024-11-21-1312_4-CapObj_0000.FIT')
hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\\\.FIT')
hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\\\.FIT')
hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\\\.FIT')
hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\\\.FIT')
hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\\\.FIT')
hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\\\.FIT')

def single(x,I_0,a,b):
    theta = np.arctan((2*np.array(x)-b)/86000)
    beta = np.pi*a*np.sin(theta)/1.06
    return I_0*((np.sin(beta))/beta)**2

def double(x,I_0,a,b,L,c):
    theta = np.arctan((2*np.array(x)-b)/L)
    beta = np.pi*a*np.sin(theta)/1.06
    gamma = np.pi*c*np.sin(theta)/1.06
    return I_0*(((np.sin(beta))/beta)**2)*(np.cos(gamma))**2

def gauss(x,I_0,a,b):
    return I_0*np.exp(-((x-a)/(np.sqrt(2)*b))**2)

def fit():
    X = np.arange(0, 3840, 1)
    Y = np.arange(0,2160, 1)
    Xmesh, Ymesh = np.meshgrid(X, Y)
    Z = np.array(hdul1[0].data[0:2160,0:3840])

    argpeak = np.unravel_index(np.argmax(Z, axis=None), Z.shape)

    Zx = np.array(hdul1[0].data[argpeak[0],0:3840])
    Zy = np.array(hdul1[0].data[0:2160,argpeak[1]])

    xHMarray = [Zx[i] for i in range(len(Zx)) if Zx[i]>(np.max(Zx)/3)]
    xFWHMapprox = len(xHMarray)
    xSigmaApprox =  xFWHMapprox/(2*np.sqrt(2*np.log(2)))

    yHMarray = [Zy[i] for i in range(len(Zy)) if Zy[i]>(np.max(Zy)/3)]
    yFWHMapprox = len(yHMarray)
    ySigmaApprox =  yFWHMapprox/(2*np.sqrt(2*np.log(2)))

    sigmaAvg = math.ceil((xSigmaApprox+ySigmaApprox)/2)
    print(sigmaAvg)

    xFocus = X[argpeak[1]-200:argpeak[1]+200]
    yFocus = Y[argpeak[0]-200:argpeak[0]+200]
    ZxFocus = Zx[argpeak[1]-200:argpeak[1]+200]
    ZyFocus = Zy[argpeak[0]-200:argpeak[0]+200]

    poptx,pcovx = curve_fit(gauss, xFocus, ZxFocus,[np.max(ZxFocus),argpeak[1],xSigmaApprox],bounds = ([np.max(ZxFocus)-10,0,xSigmaApprox],[2*np.max(ZxFocus),10000,10000]))
    popty,pcovy = curve_fit(gauss, yFocus, ZyFocus,[np.max(ZyFocus),argpeak[0],ySigmaApprox],bounds = ([np.max(ZyFocus)-10,0,ySigmaApprox],[2*np.max(ZyFocus),10000,10000]))

    #poptx,pcovx = curve_fit(gauss, xFocus, ZxFocus,[np.max(ZxFocus),argpeak[1],sigmaAvg],bounds = ([np.max(ZxFocus)-10,0,sigmaAvg],[2*np.max(ZxFocus),10000,10000]))
    #popty,pcovy = curve_fit(gauss, yFocus, ZyFocus,[np.max(ZyFocus),argpeak[0],sigmaAvg],bounds = ([np.max(ZyFocus)-10,0,sigmaAvg],[2*np.max(ZyFocus),10000,10000]))

    text = "Aperture wide open, collimator three turns left"
    fig2 = plt.figure(dpi = 200)
    plt.plot(xFocus,ZxFocus)
    plt.plot(xFocus,gauss(xFocus, *poptx),label = f"Parameters: I_0 = {round(poptx[0])} \n mean = {round(poptx[1],1)} \n std = {round(poptx[2],2)}")
    plt.title(f"Data and Fit using a gaussian approximation for the X direction. \n" + text)
    plt.xlabel("Pixel bin")
    plt.ylabel("Intensity")
    plt.legend(loc = 1, bbox_to_anchor=(1, 1), fontsize = 9)

    fig3 = plt.figure(dpi = 200)
    plt.plot(yFocus, ZyFocus)
    plt.plot(yFocus,gauss(yFocus, *popty),label = f"Parameters: I_0 = {round(popty[0])} \n mean = {round(popty[1],1)} \n std = {round(popty[2],2)}")
    plt.title(f"Data and Fit using gaussian approximation for the Y direction. \n" + text)
    plt.xlabel("Pixel bin")
    plt.ylabel("Intensity")
    plt.legend(loc = 1, bbox_to_anchor=(1, 1), fontsize = 9)
    plt.show()

fit()
