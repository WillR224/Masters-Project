import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.special as scpS
from scipy.optimize import curve_fit

Dir = r'C:\\Users\\willr\\Desktop\\Work\\Year 4\\Masters Project\\Plots\\Fit data.csv'
reader = pd.read_csv(Dir, skiprows=0)
data = reader.to_numpy()
data_array = np.array(data)

heights = np.array(data_array[:,1])
xSig = np.array(data_array[:,2])
ySig = np.array(data_array[:,3])

array1 = np.array([np.abs(heights[0:3]-heights[0]),xSig[0:3],ySig[0:3]])
array2 = np.array([np.abs(heights[3:6]-heights[3]),xSig[3:6],ySig[3:6]])
array3 = np.array([np.abs(heights[6:9]-heights[6]),xSig[6:9],ySig[6:9]])
array4 = np.array([np.abs(heights[9:12]-heights[9]),xSig[9:12],ySig[9:12]])


print(array1,array2,array3,array4)
plt.title("Plot of Height against beam width for varing collimator conditions \n with aperture fixed wide open")
plt.xlabel("Distance from focus in motor steps")
plt.ylabel("Std of gaussian fit in pixel bins")
plt.plot(array1[0],array1[1], label = 'Fully right, x-direction', marker = "x")
plt.plot(array2[0],array2[1], label = 'One turn left, x-direction', marker = "x")
plt.plot(array3[0],array3[1], label = 'Two turns left, x-direction', marker = "x")
plt.plot(array4[0],array4[1], label = 'Fully left, x-direction', marker = "x")
plt.plot(array1[0],array1[2], label = 'Fully right, y-direction', marker = "x")
plt.plot(array2[0],array2[2], label = 'One turn left, y-direction', marker = "x")
plt.plot(array3[0],array3[2], label = 'Two turns left, y-direction', marker = "x")
plt.plot(array4[0],array4[2], label = 'Fully left, y-direction', marker = "x")
plt.legend(loc = 1, bbox_to_anchor=(1, 0.42), fontsize = 10)
plt.show()