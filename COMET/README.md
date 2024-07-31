# COMET - Cellular cOverage MEasurement kiT
This COMET software is used by the kit to perform measurements and provides a few useful scripts.
To function, it must be installed on the Raspberry Pi of the kit as explained below.

For more details on COMET, refer to 
[its full documentation](../Documentation/doc_COMET_2024-07-30.pdf).

## Installation
While COMET source code provides relatively easy to use installation scripts
they heavily depend on correctly following all assembly steps of COMET beforehand.

To learn how to install the COMET software, please refer to the "Assembling 
COMET" section of the 
[COMET documentation](../Documentation/doc_COMET_2024-07-30.pdf).

## Requirements
The measurements program requires Python 3.9 to function as well as a few external packages described
in the [requirements.txt](./requirements.txt) file. These requirements as well as the necessary
Python version will be installed automatically when using the installation scripts. A more detailed
description of each package can be found in the [documentation](../Documentation/doc_COMET_2024-07-30.pdf).

## Usage
This section assumes that COMET is fully assembled and its software installed and configured
following the [documentation](../Documentation/doc_COMET_2024-07-30.pdf).

Before doing measurements, connect the Raspberry Pi to the Internet with an Ethernet cable and plug in
the power supply to both the RPI and the 5G HAT with two USB-C cables. After some time,
the **red LED** will turn on for at least 30 seconds. If both LEDs stay off for more than 1 minute,
unplug the power supply, wait for a few seconds a plug it back again. Wait until the **green LED**
lights up and stays on. Once it is, shutdown COMET by holding the control button 
(the one installed during assembly) for 2 seconds, then unplug the power supply. 
This step is optional but is required to update the internal clock and to use correct dates.

Bring the kit outside and place the GPS antenna at 30-50 centimeters away from the kit, black side up.
The antenna must have a large part of the sky visible, don't be too close to high building, don't
or block the antenna in any way.

Plug in the power supply. Wait until the **red LED** is off and the **green LED** is continuously on.
If the red LED stays on for more than a minute, check if the 5G HAT has power supply plugged in and
if it is properly connected to the RPI through USB-A ports. Once the green LED is on, press the
control button once. This will start a measurements session.

At first, the green LED will turn off and the red LED will start blinking. This indicates the initial
setup of the module. Usually it takes between 30 and 200 seconds, most of that time is waiting
for a GPS signal, indicated by slow blinking (see the Control Interface section below or in the documentation).

Once the setup is complete, the red LED will stop blinking and the green LED will start flashing
shortly every second. This indicates that measurements are ongoing. At that point you can move with
the kit anywhere outside to perform measurements.

When you want to stop the measurements session, press the control button once. The green LED will
blink fast for a short period of time, then stay on continuously, indicating that the session is finished
and a new one is ready to start.

Plug in an Ethernet cable and connect to the RPI through SSH with your computer. Execute 
`comet.sh transfer` to retrieve measurements.


## Control Interface
### Control button
The button allows the user to start and stop a measurement session as well as gracefully
shutdown COMET. 

| Action             | Meaning                                                                 |
|--------------------|-------------------------------------------------------------------------|
| Single press       | Start a new measurement session or stop the current measurement session |
| Hold for 2 seconds | Shut down COMET                                                         |

### Red LED
The red LED indicates when COMET is not yet ready to start measurements (at start-up,
during setup of a measurements session) and lack of signal (during measurements).

| Duration                                              | Meaning                                |
|-------------------------------------------------------|----------------------------------------|
| Always on                                             | Initialization or no module connection |
| On for 500ms, off for 3,000ms                         | Absence of GPS signal                  |
| On for 3,000ms, off for 500ms                         | Absence of network signal              |
| On for 500ms, off for 500ms                           | Absence of both network and GPS signal |
| On for 1,000ms, off for 1,000ms                       | SIM card is still locked               |
| On for 100ms, off for 100ms, for a total of 5 seconds | Wrong pin code format                  |

### Green LED
The green LED is used to indicate readiness and normal execution of measurements.

| Duration                                                                   | Meaning                                  |
|----------------------------------------------------------------------------|------------------------------------------|
| Always on                                                                  | Ready to start                           |
| Short flash every second (on for less than 100ms, off for more than 900ms) | A measurement session is ongoing         |
| On for 100ms, off for 100ms                                                | The measurements file is being converted |

## comet.sh script
The [comet.sh](./comet.sh) is used by COMET to start the main program, but it also provides multiple
utility functions which can be invoked using different arguments. To use, connect to the RPI
(through SSH or with a screen) and run the script with chosen argument:

* `comet.sh run` runs the main non-interactive program. Only works if the COMET 
service was stopped using `sudo systemctl stop comet` command.
* `comet.sh run-interactive` argument start the interactive version of the program. 
Only works if the COMET service was stopped using `sudo systemctl stop comet` command.
* `comet.sh update` updates all project files including `comet.sh` script from your 
computer. It assumes that the project files on your computer as stored in the directory from 
which COMET software was installed. If files are not located there, the path must be changed 
manually in the `USER_DIR` variable at the start of the script. Note that It will also update 
the running `comet.sh` script, which might display errors in the terminal or even start the 
main program by accident. Despite that, all files will be copied without issues. 
* `comet.sh update-full` updates all project files and installs necessary
python packages. This requires Internet connection.
* `comet.sh clean` removes all measurements (COMET and converted) and log files from 
the RPI. 
* `comet.sh transfer` transfers all measurements (COMET and converted) and log files
to your computer, to the installation directory indicated by the `USER_DIR` variable.
* Using no arguments is generally reserved for the program start at boot, but can also be used
as alternative to the `run` argument.

## COMET measurements converter
COMET software provides a Python script that allows to convert the COMET measurements files to
CORENTIN-compatible "cev" files. It is integrated in the main measurements program to convert
the measurements at the end of each session.

The converter can also be used independently of COMET. It requires no external
packages and can be used on any computer with Python 3.6 or above. Its only dependency
is the [utils.py](./src/utils.py) module.

A measurements file can be converted either through code or by executing the 
[CometToCevConverter.py](./src/CometToCevConverter.py) module. When executing the module with
`python ./src/CometToCevConverter.py`, you will be prompted to choose a COMET measurements file.
After that, the converted file will be stored under the `cev` directory, in a folder with current
date as name.

To convert a measurements file from code, import the CometToCevConverter class from the CometToCevConverter.py
module and create an instance of it using a `with` statement and the path to the measurements file.
Then call the `process()` method of that instance. See example below:

```python
from CometToCevConverter import CometToCevConverter
with CometToCevConverter("/path/to/measurements/file") as converter:
    converter.process()
```

In both cases, make sure that [CometToCevConverter.py](./src/CometToCevConverter.py) has access 
to the [utils.py](./src/utils.py) module, for example by placing both of them in the same directory.