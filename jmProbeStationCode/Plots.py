#!/usr/bin/python
# Plots.py -- contains classes for IV and CV plots using matplotlib
# Updated: 01/03/2021
# Contributing: Matt Basso (University of Toronto), Will George (University of Birmingham)

import matplotlib.pyplot as plt
import time

class IVTimePlot(object):
    ''' Plot temperature, relative humidity, current and voltage as functions of time '''

    def __init__(self, title="IV Time Data"):
        plt.ion()
        self.mainplt, self.subplt = plt.subplots(4, sharex=True)
        self.mainplt.suptitle(title)
        self.lines0, = self.subplt[0].plot([], [], 'o')
        self.lines1, = self.subplt[1].plot([], [], 'o')
        self.lines2, = self.subplt[2].plot([], [], 'o')
        self.lines3, = self.subplt[3].plot([], [], 'o')
        self.mainplt.subplots_adjust(hspace=0.1)
        for sub in self.subplt:
            sub.set_autoscalex_on(True)
            sub.set_autoscaley_on(True)
        self.subplt[-1].set_xlabel('Time [s]')
        self.subplt[0].set_ylabel('Temperature [C]')
        self.subplt[1].set_ylabel('Humidity [%]')
        self.subplt[2].set_ylabel('Current [uA]')
        self.subplt[3].set_ylabel('Voltage [V]')
        for sub in self.subplt:
            sub.set_autoscalex_on(True)
            sub.set_autoscaley_on(True)
        self.timedata = []
        self.Tdata = []
        self.RHdata = []
        self.Idata = []
        self.Vdata = []
        self.t0 = float(time.time() )

    def update(self, measurement):
        t_new = float(time.time() )
        self.timedata.append(t_new - self.t0)
        self.Vdata.append(1* float(measurement[1]) )
        self.Idata.append(1e6 * float(measurement[2]) )
        self.Tdata.append(float(measurement[3]) )
        self.RHdata.append(float(measurement[4]) )
        self.lines0.set_xdata(self.timedata)
        self.lines1.set_xdata(self.timedata)
        self.lines2.set_xdata(self.timedata)
        self.lines3.set_xdata(self.timedata)
        self.lines0.set_ydata(self.Tdata)
        self.lines1.set_ydata(self.RHdata)
        self.lines2.set_ydata(self.Idata)
        self.lines3.set_ydata(self.Vdata)
        for sub in self.subplt:
            sub.relim()
            sub.autoscale_view()
        self.mainplt.canvas.draw()
        self.mainplt.canvas.flush_events()

    def savefig(self, name='timeplot.png'):
        self.mainplt.savefig(name)

    def close(self):
        plt.close()


class TwoIVPlotWindow(object):
    ''' Plot two IV curves '''

    def __init__(self, title="IV Data"):
        plt.ion()
        self.mainplt, self.subplt = plt.subplots(2, sharex=True)
        self.mainplt.suptitle(title)
        self.lines0, = self.subplt[0].plot([], [], 'o')
        self.lines1, = self.subplt[1].plot([], [], 'o')
        self.mainplt.subplots_adjust(hspace=0.1)
        for sub in self.subplt:
            sub.set_autoscalex_on(True)
            sub.set_autoscaley_on(True)
        self.subplt[-1].set_xlabel('PS voltage [V]')
        self.subplt[0].set_ylabel('Current 1 [uA]')
        self.subplt[1].set_ylabel('Current 2 [uA]')
        for sub in self.subplt:
            sub.set_autoscalex_on(True)
            sub.set_autoscaley_on(True)
        self.IPSdata = []
        self.IAMdata = []
        self.Vdata = []

    def update(self, measurement):
        self.Vdata.append(1* float(measurement[0]) )
        self.IAMdata.append(1e6 * float(measurement[1]) )
        self.IPSdata.append(1e6 * float(measurement[2]) )
        self.lines0.set_xdata(self.Vdata)
        self.lines1.set_xdata(self.Vdata)
        self.lines0.set_ydata(self.IAMdata)
        self.lines1.set_ydata(self.IPSdata)
        for sub in self.subplt:
            sub.relim()
            sub.autoscale_view()
        self.mainplt.canvas.draw()
        self.mainplt.canvas.flush_events()

    def savefig(self, name='Two_IV_plots.png'):
        self.mainplt.savefig(name)

    def close(self):
        plt.close()


class IVPlotWindow(object):
    ''' Plot current as a function of voltage '''

    def __init__(self):
        pass

    # Generate the plot window
    def open(self):
        plt.ion()
        self.mainplt = plt.figure()
        self.subplt = self.mainplt.add_subplot(111)
        self.mainplt.suptitle('IV measurement')
        self.lines, = self.subplt.plot([], [], 'o')
        self.subplt.set_autoscalex_on(True)
        self.subplt.set_autoscaley_on(True)
        self.subplt.set_xlabel('Voltage V [V]')
        self.subplt.set_ylabel('Current I [uA]')
        self.Vdata = []
        self.Idata = []

    # Update the opened plot with data
    def update(self, measurement):
        self.Vdata.append(1 * float(measurement[1]))
        self.Idata.append(1e6 * float(measurement[2]))
        self.lines.set_xdata(self.Vdata)
        self.lines.set_ydata(self.Idata)
        self.subplt.relim()
        self.subplt.autoscale_view()
        self.mainplt.canvas.draw()
        self.mainplt.canvas.flush_events()

    # Close the plot window
    def close(self):
        plt.close()


class CVPlotWindow(object):
    ''' Plot capacitance, 1/(capacitance)^2, resistance and current as functions of time '''

    def __init__(self):
        pass

    # Generate the plot window
    def open(self): #,equiv_circuit):
        plt.ion()
        equiv_circuit = None
        self.mainplt, self.subplt = plt.subplots(4, sharex = True)
        self.mainplt.suptitle('CV measurement')
        self.lines0, = self.subplt[0].plot([], [], 'o')
        self.lines1, = self.subplt[1].plot([], [], 'o')
        self.lines2, = self.subplt[2].plot([], [], 'o')
        self.lines3, = self.subplt[3].plot([], [], 'o')
        self.subplt[0].set_autoscalex_on(True)
        self.subplt[1].set_autoscalex_on(True)
        self.subplt[2].set_autoscalex_on(True)
        self.subplt[3].set_autoscalex_on(True)
        self.subplt[0].set_autoscaley_on(True)
        self.subplt[1].set_autoscaley_on(True)
        self.subplt[2].set_autoscaley_on(True)
        self.subplt[3].set_autoscaley_on(True)
        self.subplt[3].set_xlabel('Voltage V [V]')
        self.subplt[0].set_ylabel('C [pF]')
        self.subplt[2].set_ylabel('R [kOhms]')
        if equiv_circuit == 'PAR':
            self.subplt[0].set_ylabel('C_P [pF]')
            self.subplt[2].set_ylabel('R_P [kOhms]')
        if equiv_circuit == 'SER':
            self.subplt[0].set_ylabel('C_S [pF]')
            self.subplt[2].set_ylabel('R_S [kOhms]')
        self.subplt[1].set_ylabel('1/C^2 [1/pF^2]')
        self.subplt[3].set_ylabel('Current I [uA]')
        self.Vdata = []
        self.Cdata = []
        self.C2data = []
        self.Idata = []
        self.Rdata = []

    # Update the opened plot with data
    def update(self, measurement):
        self.Vdata.append(1 * float(measurement[1]))
        self.Cdata.append(1e12 * float(measurement[3]))
        invC2 = 1/(float(measurement[3])*float(measurement[3]))
        self.C2data.append(invC2) 
        self.Idata.append(1e6 * float(measurement[2]))
        self.Rdata.append(1e-03 * float(measurement[4]))
        self.lines0.set_xdata(self.Vdata)
        self.lines0.set_ydata(self.Cdata)
        self.lines1.set_xdata(self.Vdata)
        self.lines1.set_ydata(self.C2data)
        self.lines2.set_xdata(self.Vdata)
        self.lines2.set_ydata(self.Rdata)
        self.lines3.set_xdata(self.Vdata)
        self.lines3.set_ydata(self.Idata)
        self.subplt[0].relim()
        self.subplt[0].autoscale_view()
        self.subplt[1].relim()
        self.subplt[1].autoscale_view()
        self.subplt[2].relim()
        self.subplt[2].autoscale_view()
        self.subplt[3].relim()
        self.subplt[3].autoscale_view()
        self.mainplt.canvas.draw()
        self.mainplt.canvas.flush_events()

    # Close the plot window
    def close(self):
        plt.close()
