import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.special as scpS
from scipy.optimize import curve_fit
from astropy.io import fits
from matplotlib import cm
from matplotlib.ticker import LinearLocator
import lmfit

hdul1 = fits.open(r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\CapObj\\2024-11-21_13_08_02Z\\2024-11-21-1308_0-CapObj_0000.FIT')

X = np.arange(0, 3840, 1)
Y = np.arange(0,2160, 1)

Z = np.array(hdul1[0].data[0:2160,0:3840])
argpeak = np.unravel_index(np.argmax(Z, axis=None), Z.shape)

Zx = np.array(hdul1[0].data[argpeak[0],0:3840])
Zy = np.array(hdul1[0].data[0:2160,argpeak[1]])

Xhires = np.arange(0, 3840, 0.1)
Yhires = np.arange(0, 2160, 0.1)

class SingleSlitModel(lmfit.Model):
    def __init__(self, *args, **kwargs):
        def singleSlit(x, I_0, midpoint, slitWidth):
            return I_0*((np.sin(np.pi*slitWidth*np.sin((np.arctan((2*np.array(x)-midpoint)/86000)))/1.06))/(np.pi*slitWidth*np.sin((np.arctan((2*np.array(x)-midpoint)/86000)))/1.06))**2
        super(SingleSlitModel, self).__init__(singleSlit, *args, **kwargs)

    def guess(self, data, **kwargs):
        params = self.make_params()
        def pset(param, value):
            params["%s%s" % (self.prefix, param)].set(value=value)
        pset("I_0", 60000)
        pset("midpoint", np.argmax(data))
        pset("slitWidth", 2500)
        return lmfit.models.update_param_vals(params, self.prefix, **kwargs)
    
model = SingleSlitModel()
params = model.guess(Zx, x=Zy)
fit = model.fit(Zx, params, x=X)
for key in fit.params:
    print(key, "=", fit.params[key].value, "+/-", fit.params[key].stderr)
plt.plot(X,)
plt.plot(X,fit.best_fit())