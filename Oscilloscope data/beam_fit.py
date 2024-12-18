# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 16:35:21 2024

@author: nat
"""

import imageio as iio
import laserbeamsize as lbs
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import scipy.special as scpS
from scipy.optimize import curve_fit
from astropy.io import fits
from matplotlib import cm
from matplotlib.ticker import LinearLocator
from scipy.optimize import curve_fit
from matplotlib.text import Text
#file = "cell_image_#001.bmp"
#image = iio.imread(file)
#image = Image.open('C:/Users/nat/OneDrive - University of Birmingham/PhD/Y1/Lab/beam imaging/090924/cell_20.bmp').convert('L')


# hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\height testing PiN\\2024-12-05_14_38_58Z\\2024-12-05-1438_9-CapObj_0000.FIT')
# Z = np.array(hdul1[0].data[810:860,270:330])
# image = np.asarray(Z)
# x, y, dx, dy, phi = lbs.beam_size(image)

# print("The center of the beam ellipse is at (%.0f, %.0f)" % (x, y))
# print("The ellipse diameter (closest to horizontal) is %.0f pixels" % dx)
# print("The ellipse diameter (closest to   vertical) is %.0f pixels" % dy)
# print("The ellipse is rotated %.0f° ccw from the horizontal" % (phi * 180/3.1416))

# print("dx: " + str(dx*6.45) + ', ' + str(dx*6.45/2))
# print("dy: " + str(dy*6.45)+ ', ' + str(dy*6.45/2))


# data = lbs.plot_image_analysis(image,phi=np.radians(0))
# plt.show()

def waist(z,Zr,w0):
    return w0*np.sqrt(1+(z/Zr)**2)

def chisquare(O,E,std):
    return ((O-E)/std)**2

fig, ax = plt.subplots(figsize = (12,10), dpi = 90)
#plt.suptitle("Plot of average beam radius vs position from focus with \n the aperture at 1.5cm closed", y = 1, fontsize = 20)
lambda1=1064e-9 # meters
z1_all=((np.array([10645,10695,10745,10795,10845,10895,10945,10995]))/400)*1e-3

# d1x_all=(8e-6)*np.array([10.19546189,5.848451461,4.549039087,3.360880794,2.55714514,2.465320556,2.714904323,5.221970759])
errorsx = np.array([0.2413779,0.147300369,0.097437612,0.066830196,0.048097798,0.046599202,0.068638374,0.116665859])

# d1y_all=(8e-6)*np.array([9.574100939,5.308349117,3.960313005,2.873994026,2.29509651,2.19370247,2.477889636,4.864475624])
errorsy = np.array([0.22741604,0.127834046,0.082128831,0.052592628,0.038691142,0.037941554,0.0623606,0.116314244])

d1_all = (8e-6)*np.array([9.884781415,5.578400289,4.254676046,3.11743741,2.426120825,2.329511513,2.59639698,5.043223192])
errorsall = (1/2)*np.sqrt(errorsx**2+errorsy**2)

lbs.M2_radius_plot(z1_all, d1_all, lambda1, strict=True)
s = lbs.M2_fit(z1_all, d1_all, lambda1)
print(lbs.M2_report(z1_all, d1_all, lambda1))

fitWaists = waist(((z1_all-s[0][1])*1e6),s[0][4]*1e6,1e6*s[0][0]/2)

chisquared = np.sum(chisquare(d1_all*(5e5),fitWaists,errorsall))
chidof = chisquared/(len(d1_all)-1)
print(chidof)
errorsall = errorsall*np.sqrt(chidof)
chisquared = np.sum(chisquare(d1_all*(5e5),fitWaists,errorsall))
chidof = chisquared/(len(d1_all)-1)
print(chidof)

# print(axes[1])4
#ax.errorbar((z1_all-s[0][1])*1000,d1x_all*5e5,errorsall,linestyle = '',color = "green",elinewidth=2)
print(s)
ticks1 = ax.get_xticks()
ticks2 = ax.get_yticks()
ax.set_xticks(ticks1, labels = [round(1000*ticks1[i],1) for i in range(len(ticks1))], fontsize = 18)
ax.set_yticks(ticks2, labels = [round(ticks2[i],4) for i in range(len(ticks2))], fontsize = 18)
ax.set_xlabel("Axial Location ($\mu$m)", fontsize = 18)
ax.set_ylabel("Beam Radius ($\mu$m)", fontsize = 18)
#axes[0].set_xticks(ticks2, labels = [round(ticks2[i],4) for i in range(len(ticks2))])
#axes[2].set_xticks(ticks2, labels = [round(ticks2[i],4) for i in range(len(ticks2))])
plt.text(-0.25,45,f"$Z_R$ = {round(s[0][4]*1000,4)}$\pm${round(s[1][4]*1000,4)}mm  $M^2$ = {round(s[0][3],3)}$\pm${round(s[1][3],3)}", fontsize = 18)
plt.text(-0.2,40,f"$w_0$ = $d_0$/2 = {round(1e6*s[0][0]/2,2)}$\pm${round(1e6*s[1][0]/2,2)}$\mu$m  $\lambda$ = 1064nm", fontsize = 18)
plt.text(-0.15,35, f"Errors scaled such that $\chi^2$ per dof = {round(chidof)}", fontsize = 16)
plt.text(0.20,-5, f"$\\theta$ = {round(s[0][2]*1000,1)}$\pm${round(s[1][2]*1000,1)} mrad", fontsize = 15)
ax.errorbar((z1_all-s[0][1])*1000,d1_all*5e5,errorsall,linestyle = '',color = "black")
ax.errorbar((z1_all-s[0][1])*1000,-d1_all*5e5,errorsall,linestyle = '',color = "black")
plt.show()


    



##print(z1_all,d1x_all,errorsx)
#plt.errorbar(z1_all,d1x_all,errorsx)




# x = np.sum(image, axis=0)

# image_2 = Image.open('IM2_1706_#001.bmp').convert('L')
# image_2 = np.asarray(image_2)
# x2 = np.sum(image_2, axis=0)
# plt.plot(x, label ='IM1')
# plt.plot(x2, label = 'IM2')
# plt.legend()
