# COMET - Cellular cOverage MEasurement kiT
This COMET software is used by the kit to perform measurements and provides a few useful scripts.
To function, it must be installed on the Raspberry Pi of the kit as explained below.

For more details on COMET, refer to 
[its full documentation](../Documentation/doc_COMET_2024-07-30.pdf).

## Installation
COMET software can be installed on the Raspberry Pi using installation scripts provided
with the source code: [deploy.sh](./deploy.sh) and [install.sh](./install.sh). They use
the SSH connection between your computer and the Raspberry Pi to transfer, configure and
create the necessary files.

Before using the installation scripts, a few steps need to be done:

* Modify USER_COMPUTER_IP with the IP address of your computer in the [comet.sh](./comet.sh)
script. This allows for future use of its utility functions such as easy transfer of measurements
and logs from the Raspberry Pi to your computer.
* Generate an SSH key using `ssh-keygen` command in the terminal. You will be prompted to choose
the name of the key (if left empty, id_rsa will used as name) and a password (can be left empty if
security is not a concern). 
* Copy the SSH key to the RPI: `ssh-copy-id -i ~/.ssh/id_rsa user@ip` (where `user` is the username
on the RPI and ip the RPI's IP address). You will be prompted to enter the password of the RPI
to do that but from that point all SSH connections to the RPI from this computer can be done
without entering the password.
* Do the same in the other direction by generating a key on the RPI and copying it to your computer.
This allows to avoid entering the password each time a utility function is used.

Once this is done, execute the deployment script with username and IP address of the RPI in arguments:
`deploy.sh rpi 192.168.1.2`. This will transfer the necessary files to RPI and start the
[install.sh](./install.sh) script. Make sure that the RPI has access to the Internet. This script
will install and configure all the necessary services. It will also install Python 3.11 and
the required packages if they are not present (this requires an Internet connection). Once the
installation is finished, COMET software will start, indicated by the LEDs if they are installed.

Alternatively, it is possible to install the software in an interactive mode using
the [install.sh](./install.sh) script on the RPI manually. For details, refer to the
"Interactive installation" section of the 
[COMET documentation](../Documentation/doc_COMET_2024-07-30.pdf).

## comet.sh script
The [comet.sh](./comet.sh) is used by COMET to start the main program, but it also provides multiple
utility functions which can be invoked using different arguments:

* `comet.sh run` argument runs the main non-interactive program. Only works if the COMET 
service was stopped using `sudo systemctl stop comet` command.
* `comet.sh run-interactive` argument start the interactive version of the program. 
Only works if the COMET service was stopped using `sudo systemctl stop comet` command.
* `comet.sh update` argument updates all project files including `comet.sh` script from your 
computer. It assumes that the project files on your computer as stored in the directory from 
which COMET software was installed. If files are not located there, the path must be changed 
manually in the `USER_DIR` variable at the start of the script. Note that It will also update 
the running `comet.sh` script, which might display errors in the terminal or even start the 
main program by accident. Despite that, all files will be copied without issues. 
* `comet.sh update-full` argument updates all project files and installs necessary
python packages. This requires Internet connection.
* `comet.sh clean` argument removes all measurements (COMET and converted) and log files from 
the RPI. 
* `comet.sh transfer` argument transfers all measurements (COMET and converted) and log files
to your computer, to the installation directory indicated by the `USER_DIR` variable.
* Using no arguments is generally reserved for the program start at boot, but can also be used
as alternative to the `run` argument.
