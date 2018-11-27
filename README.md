APC Network Power Management Controller
=======================================

[![Build Status](https://travis-ci.com/scls19fr/APC.svg?branch=master)](https://travis-ci.com/scls19fr/APC)

Controls rebooting of APC network PDU switches with 'telnet' network interface.
Tested with the AP7900, but likely works with other models.

This handles locking of the device so that parallel calls will block, since
APC has a single telnet session.

Requirements
------------

- Python 2.x or Python 3.x
- Python Expect (pexpect) library.  To install: 'pip install pexpect'
- APC with telnet network interface (tested on AP7900)

Installation
------------

```bash
$ pip install git+https://github.com/scls19fr/APC
```

or

Download source and run

```bash
$ python setup.py install
```

The APC needs to be set up with telnet enabled, and using a fixed IP address.
If a DHCP address is used, it may change, and you will have trouble connecting.

Usage
-----

### Display help
```
$ apc --help
usage: apc [-h] [--host HOST] [--user USER] [--password PASSWORD] [-v]
           [--quiet] [--debug] [--reboot OUTLET] [--off OUTLET] [--on OUTLET]
           [--cli CLI] [--delay DELAY] [--duration DURATION] [--status]

APC Python CLI

optional arguments:
  -h, --help           show this help message and exit
  --host HOST          Override the host
  --user USER          Override the username
  --password PASSWORD  Override the password
  -v, --verbose        Verbose messages
  --quiet              Quiet
  --debug              Debug mode
  --reboot OUTLET      Reboot an outlet
  --off OUTLET         Turn off an outlet
  --on OUTLET          Turn on an outlet
  --cli CLI            command line to execute 'ssh {user}@{host}' or 'telnet
                       {host}
  --delay DELAY        delay before on/off (-1 to 7200 sec, where -1=Never)
  --duration DURATION  reboot duration (5 to 60 sec)
  --status             Status of outlets
```

### Outlet status
```
$ apc --status
Acquiring lock /tmp/apc.lock
Connecting to APC @ 10.8.0.142
Logged in as user apc, version 3.9.2
Outlet 1 NAS             ON
Outlet 2                 OFF
Outlet 3                 ON
Outlet 4                 ON
Outlet 5                 ON
Outlet 6                 ON
Outlet 7                 ON
Outlet 8                 ON
DISCONNECTED from 10.8.0.142
```

### Power cycle (reboot) a single port
#### Immediate
```$ apc --reboot PORT```

Example: reboot power port 8
```
$ apc --reboot 8
Acquiring lock /tmp/apc.lock
Connecting to APC @ 10.8.0.142
Logged in as user apc, version 3.9.2
APC 10.8.0.142: Outlet #8 Rebooted
DISCONNECTED from 10.8.0.142
```

#### Delayed reboot with duration
Example: reboot power port 4

```$ apc --reboot 4 --delay 30 --duration 10```

### Power off a single port
#### Immediate
Example: power off port 4

```$ apc --off 4```

#### Delayed power off
Example: power off port 4 30 seconds later

```$ apc --off 4 --delay 30```

Environment Variables
---------------------

The following environment variables will override the APC connection:
- `$APC_HOST`
- `$APC_USER`
- `$APC_PASSWORD`
