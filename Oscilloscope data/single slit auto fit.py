import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.special as scpS
import scipy.integrate as scpI
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
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_44_08Z\\2024-11-21-1344_1-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_45_28Z\\2024-11-21-1345_4-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_46_29Z\\2024-11-21-1346_4-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_49_04Z\\2024-11-21-1349_0-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_47_20Z\\2024-11-21-1347_3-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_50_01Z\\2024-11-21-1350_0-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_52_35Z\\2024-11-21-1352_5-CapObj_0000.FIT')
#hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_14_13_38Z\\2024-11-21-1413_6-CapObj_0000.FIT')

# hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_23_41Z\\2024-11-26-0923_6-CapObj_0000.FIT')
# hdul2 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_26_13Z\\2024-11-26-0926_2-CapObj_0000.FIT')
# hdul3 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_27_29Z\\2024-11-26-0927_4-CapObj_0000.FIT')

# hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_31_18Z\\2024-11-26-0931_3-CapObj_0000.FIT')
# hdul2 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_32_00Z\\2024-11-26-0932_0-CapObj_0000.FIT')
# hdul3 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_33_02Z\\2024-11-26-0933_0-CapObj_0000.FIT')

# hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_35_07Z\\2024-11-26-0935_1-CapObj_0000.FIT')
# hdul2 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_36_09Z\\2024-11-26-0936_1-CapObj_0000.FIT')
# hdul3 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_37_33Z\\2024-11-26-0937_5-CapObj_0000.FIT')

# hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_40_21Z\\2024-11-26-0940_3-CapObj_0000.FIT')
# hdul2 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_41_12Z\\2024-11-26-0941_2-CapObj_0000.FIT')
# hdul3 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_43_42Z\\2024-11-26-0943_7-CapObj_0000.FIT')

hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_43_42Z\\2024-11-26-0943_7-CapObj_0000.FIT')
hdul2 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_44_07Z\\2024-11-26-0944_1-CapObj_0000.FIT')
hdul3 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-26_09_54_14Z\\2024-11-26-0954_2-CapObj_0000.FIT')


# hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\')
# hdul2 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\')
# hdul3 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\')

HDUlist = [hdul1,hdul2,hdul3]


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


def errorssig(cov_matrix):
    varb = cov_matrix[2][2]
    sigerror = np.sqrt(varb)
    return sigerror

def fit(hdul,text):
    X = np.arange(0, 3840, 1)
    Y = np.arange(0,2160, 1)
    Xmesh, Ymesh = np.meshgrid(X, Y)
    Z = np.array(hdul[0].data[0:2160,0:3840])

    argpeak = np.unravel_index(np.argmax(Z, axis=None), Z.shape)

    Zx = np.array(hdul[0].data[argpeak[0],0:3840])
    Zy = np.array(hdul[0].data[0:2160,argpeak[1]])

    xHMarray = [Zx[i] for i in range(len(Zx)) if Zx[i]>(np.max(Zx)/2)]
    xFWHMapprox = len(xHMarray)
    xSigmaApprox =  xFWHMapprox/(2*np.sqrt(2*np.log(2)))

    yHMarray = [Zy[i] for i in range(len(Zy)) if Zy[i]>(np.max(Zy)/2)]
    yFWHMapprox = len(yHMarray)
    ySigmaApprox =  yFWHMapprox/(2*np.sqrt(2*np.log(2)))

    xFocus = X[argpeak[1]-200:argpeak[1]+200]
    yFocus = Y[argpeak[0]-200:argpeak[0]+200]
    ZxFocus = Zx[argpeak[1]-200:argpeak[1]+200]
    ZyFocus = Zy[argpeak[0]-200:argpeak[0]+200]

    poptx,pcovx = curve_fit(gauss, xFocus, ZxFocus,[np.max(ZxFocus),argpeak[1],xSigmaApprox],bounds = ([np.max(ZxFocus),0,xSigmaApprox],[2*np.max(ZxFocus),10000,10000]))
    popty,pcovy = curve_fit(gauss, yFocus, ZyFocus,[np.max(ZyFocus),argpeak[0],ySigmaApprox],bounds = ([np.max(ZyFocus),0,ySigmaApprox],[2*np.max(ZyFocus),10000,10000]))
    print(errorssig(pcovx),errorssig(pcovy))
    #poptx,pcovx = curve_fit(gauss, xFocus, ZxFocus,[np.max(ZxFocus),argpeak[1],sigmaAvg],bounds = ([np.max(ZxFocus)-10,0,sigmaAvg],[2*np.max(ZxFocus),10000,10000]))
    #popty,pcovy = curve_fit(gauss, yFocus, ZyFocus,[np.max(ZyFocus),argpeak[0],sigmaAvg],bounds = ([np.max(ZyFocus)-10,0,sigmaAvg],[2*np.max(ZyFocus),10000,10000]))

    fig2 = plt.figure(dpi = 200)
    plt.plot(xFocus,ZxFocus)
    plt.plot(xFocus,gauss(xFocus, *poptx),label = f"Parameters: I_0 = {round(poptx[0])} \n mean = {round(poptx[1],1)} \n std = {round(poptx[2],2)}")
    plt.title(f"Data and Fit using a gaussian approximation for the X direction. \n" + text)
    plt.xlabel("Pixel bin")
    plt.ylabel("Intensity")
    plt.legend(loc = 1, bbox_to_anchor=(1, 1), fontsize = 9)
    plt.savefig(autoPlotsDir+filename+r"X.svg")

    fig3 = plt.figure(dpi = 200)
    plt.plot(yFocus, ZyFocus)
    plt.plot(yFocus,gauss(yFocus, *popty),label = f"Parameters: I_0 = {round(popty[0])} \n mean = {round(popty[1],1)} \n std = {round(popty[2],2)}")
    plt.title(f"Data and Fit using gaussian approximation for the Y direction. \n" + text)
    plt.xlabel("Pixel bin")
    plt.ylabel("Intensity")
    plt.legend(loc = 1, bbox_to_anchor=(1, 1), fontsize = 9)
    plt.savefig(autoPlotsDir+filename+r"Y.svg")
    return (poptx[2],popty[2])

def ISOstandard(hdul):
    X = np.arange(0, 3840, 1)
    Y = np.arange(0,2160, 1)
    Xmesh, Ymesh = np.meshgrid(X, Y)
    Z = np.array(hdul[0].data[0:2160,0:3840])
    argpeak = np.unravel_index(np.argmax(Z, axis=None), Z.shape)
    X = X - argpeak[1]
    Y = (Y - (2160-argpeak[0]))
    Ixsquared = scpI.simps(scpI.simps((X**2)*Z,X),Y)
    I = scpI.simps(scpI.simps(Z,X),Y)
    wx = 2*np.sqrt(Ixsquared/I)
    return wx

globalDir = r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Oscilloscope data\\height testing PiN\\'
localDir = r"2024-12-05_14_56_09Z\\2024-12-05-1456_1-CapObj_0000"
file = globalDir + localDir + r".FIT"
print(file)
hdul1 = fits.open(file)
autoPlotsDir = r"C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Plots\\Autoplots\\"
text = ""
filename = r"2024-12-05-1456"
sigx,sigy = fit(hdul1,text)


plt.show()
