# COMET - Cellular cOverage MEasurement kiT

## Installation
* Exchange ssh keys between the developer computer and the Raspberry Pi
* Modify DEV_COMPUTER_IP, DEV_COMPUTER_USER, SOURCE_DIR, DEST_DIR
variables with your values in [run.sh](./run.sh).
* Transfer the shell script to the Raspberry Pi computer 
in DEST_DIR directory manually (for example with scp command)
* Execute `./run.sh update-full` on the Raspberry Pi (from an SSH connection
or using a keyboard with a screen). This will copy all the necessary
files to the RPI.
* Run the program using `./run.sh` with no arguments.

## Run.sh arguments
* `run` argument updates the python files of the project from 
the project directory on the developer computer and runs the project
* `update` argument updates the python files as well as the `run.sh` script
but does not run the program
* `update-full` argument updates all files from the project directory,
including the python virtual environment (.venv) but does not run the program
* `clean` argument removes all temporary measurements files 
(prefixed with tmp_)
* `transfer` argument transfers all measurements to the developer computer
* Using no arguments runs the program directly without trying to update files
