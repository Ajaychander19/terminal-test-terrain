# COMET - Cellular cOverage MEasurement kiT

## Installation
* Exchange ssh keys between the developer computer and the Raspberry Pi
and connect to the RPI with SSH
* Modify DEV_COMPUTER_IP, DEV_COMPUTER_USER, SOURCE_DIR, DEST_DIR
variables with your values in [comet.sh](./comet.sh).
* Transfer the shell script to the Raspberry Pi computer 
in DEST_DIR directory manually (for example with scp command)
* Create a Python virtual environment: `python -m venv .venv`
* Execute `./comet.sh update-full` on the Raspberry Pi. 
This will copy all the necessary files to the RPI and install 
necessary python packages. This requires an internet connection on the RPI.
* To be able to execute the program on the RPI without continuous SSH
connection, replace 
* Run the program using `./comet.sh` with no arguments to start measurements
in automatic mode or `./comet.sh simple` to enter interactive mode.

## Run.sh arguments
* `run` argument updates the python files of the project from 
the project directory on the developer computer and runs the interactive version
of the project, allowing sending any AT commands or doing measurements
for any amount of time
* `simple` argument start the interactive version of the project without
updating any files (useful when ssh connection is not configured)
* `update` argument updates project files including `comet.sh` script
but does not run the program and doesn't install packages
* `update-full` argument updates all project files and install necessary
python packages
* `clean` argument removes all temporary measurements files 
(prefixed with tmp_)
* `transfer` argument transfers all measurements to the developer computer
* Using no arguments runs the automatic version of the project
directly without trying to update files
