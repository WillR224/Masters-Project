# hardware-scripts

## Python scripts for IVs and CVs

The following python scripts can be used for running IV and CV measurements:

 - `Interfaces.py` contains class wrappers for interfacing with sockets, serial ports, and GPIB connections.
 - `Plots.py` contains classes for IV and CV plots produced using matplotlib.
 - `Devices.py` contains class wrappers for the following measurement instruments: Keithley 2410 sourcemeter, Keithley 6487 picoammeter, Keithley 6517 electrometer, Keysight E4980AL LCR, WayneKerr 6500B LCR.
 - `MeasurementFunctions.py` contains classes for running IV and CV tests.
 - `runIVCV.py` is the main script which establishes connections to instruments and runs tests.

The functions within `MeasurementFunctions.py` perform IV and CV tests and write the data to a text file. They perform ramping of the power supplies where necessary and save any plots produced during the measurement. The tests implemented are as follows:
 - `measureIV_PS` - IV with single power supply to apply voltage and measure current, starting from 0V.
 - `measureIV_SMU` - IV using two power supplies; one applies a fixed voltage while the other performs IV sweep.
 - `measureIV_MD8` - IV using two power supplies; the first performs an IV sweep, the second also measures the current.
 - `measureCV` - CV sweep using a power supply and an LCR meter.
 - `measureCV_SMU` - CV with two power supplies and an LCR meter; first power supply applies a fixed voltage, the second is used to perform a CV sweep.
 
### Running the scripts:

Connections to the instruments and the running of tests is handled by the `runIVCV.py` script. Currently the `measureIV_PS`, `measureIV_SMU` and `measureCV` functions can be run from this script as follows:
~~~
python runIVCV.py IV
python runIVCV.py IV_SMU
python runIVCV.py CV
~~~
Settings for the tests (initial and final voltages, instrument compliance and the like) should can be changed in `runIVCV.py`.

### Further information

The measurement scripts produce plots using the matplotlib package. This can be installed from the command line with 'pip install matplotlib' and more information can be found at https://matplotlib.org/. For the interfacing with the measurement instruments the following modules are should also be installed: socket, Serial, visa, pyvisa. Currently connection to Keithley 2410 power supply is set up to use RS232 connection which uses a serial port, interfaced by the serial module. Connection to the other instruments is set up to use GPIB using the pyVISA module. The connection type an instrument uses can be modified in the `Devices.py` classes.

These scripts have been tested on a Windows machine to make use of drivers provided by National Instruments to use a GPIB controller to communicate with the measurement instruments. To use a GPIB connection, the NI-VISA driver needs to be installed. The downloads can be found at https://www.ni.com/en-gb/support/downloads/drivers.html. The first can be found at https://www.ni.com/en-gb/support/downloads/drivers/download.ni-visa.html. This will launch the NI package manager and ask which software to install. These scripts have been tested with NI-VISA 19.5. This will also install the NI MAX programme which is very useful for testing communication with the instruments, regardless of connection type. The second driver needed is NI-488.2 which allows Windows to connect with the GPIB controller. Proceed with installation as recommended by the package manager.
