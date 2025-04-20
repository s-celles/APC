"""
APC Network PDU Controller

Payton Quackenbush
Modified by Sebastien Celles

Tested with AP7900, but should work with similar models.
"""

import os
import re
import time
import pexpect
from apc.lockfile import FilesystemLock
from apc.outlet import Outlet, Outlets


APC_ESCAPE = "\033"

APC_YES = "YES"
APC_LOGOUT = "4"

APC_VERSION_PATTERN = re.compile(r" v(\d+\.\d+\.\d+)")
APC_USERTYPE_PATTERN = re.compile(r"User : ([a-zA-Z ]*)")

APC_DEFAULT_HOST = os.environ.get("APC_HOST", "192.168.1.2")
APC_DEFAULT_USER = os.environ.get("APC_USER", "apc")
APC_DEFAULT_PASSWORD = os.environ.get("APC_PASSWORD", "apc")

LOCK_PATH = "/tmp/apc.lock"
LOCK_TIMEOUT = 60


def APC(host, user, password, verbose=False, quiet=False, cli=""):
    factory = APCFactory()
    apc = factory.build(host, user, password, verbose, quiet, cli)
    return apc


class APCLock:
    def __init__(self, quiet):
        self.quiet = quiet

    def lock(self):
        self.info("Acquiring lock %s" % (LOCK_PATH))

        self.lock = FilesystemLock(LOCK_PATH)

        count = 0
        while not self.lock.lock():
            time.sleep(1)
            count += 1
            if count >= LOCK_TIMEOUT:
                raise SystemError("Cannot acquire %s\n" % (LOCK_PATH))

    def unlock(self):
        self.lock.unlock()

    def info(self, msg):
        if not self.quiet:
            print(msg)


class APCFactory:
    def build(self, host, user, password, verbose, quiet, cli):
        self.quiet = quiet

        self.lock = APCLock(quiet)
        self.lock.lock()

        self.info("Connecting to APC @ %s" % host)
        if cli == "":
            commandline = "telnet %s" % host
        else:
            commandline = cli.format(host=host, user=user, password=password)
        if verbose:
            print("Running '%s'" % commandline)
        child = pexpect.spawn(commandline)

        child.timeout = 10
        child.setecho(True)

        child.expect("User Name : ")
        child.send(user + "\r\n")
        child.before
        child.expect("Password  : ")
        child.send(password + "\r\n")

        child.expect("Communication Established")

        header = child.before

        match = APC_VERSION_PATTERN.search(str(header))

        if not match:
            raise Exception("Could not parse APC version")

        version = match.group(1)

        self.info("Logged in as user %s, version %s" % (user, version))

        if version[0] == "3":
            apc = APC3(host, verbose, quiet)
        else:
            apc = APC2(host, verbose, quiet)

        apc.child = child
        apc.version = version
        apc.lock = self.lock

        usertype_match = APC_USERTYPE_PATTERN.search(str(header))
        if usertype_match:
            apc.admin = usertype_match.group(1).rstrip() == "Administrator"
        else:
            print("Failed to find user type header!")
            apc.admin = False

        return apc

    def info(self, msg):
        if not self.quiet:
            print(msg)


class AbstractAPC:
    def __init__(self, host, verbose, quiet):
        self.host = host
        self.verbose = verbose
        self.quiet = quiet

    def notify(self, outlet_name, state):
        print("APC %s: %s %s" % (self.host, outlet_name, state))

    def sendnl(self, a):
        self.child.send(a + "\r\n")
        if self.verbose:
            print(self.child.before)

    def get_outlet(self, outlet):
        if str(outlet) in ["*", "+", "9"]:
            return (9, "ALL outlets")
        else:
            # Assume integer outlet
            try:
                outlet = int(outlet)
                return (outlet, "Outlet #%d" % outlet)
            except Exception:
                raise SystemExit("Bad outlet: [%s]" % outlet)

    def _escape_to_main(self, depth=6):
        for i in range(depth):
            self.child.send(APC_ESCAPE)

    def set_reboot_duration(self, outlet, duration):
        pass

    def reboot_immediate(self, outlet, duration):
        (outlet, outlet_name) = self.get_outlet(outlet)

        self.set_reboot_duration(outlet, duration)

        self._escape_to_main()

        self.control_outlet(outlet)

        self.sendnl(self.APC_IMMEDIATE_REBOOT)

        self.child.expect("Immediate Reboot")
        self.sendnl(APC_YES)
        self.sendnl("")

        self.get_command_result()

        self.notify(outlet_name, "Rebooted")

        self._escape_to_main()

    def reboot_delayed(self, outlet, delay):
        raise NotImplementedError()

    def reboot(self, outlet, delay, duration):
        if delay == 0:
            self.reboot_immediate(outlet, duration)
        else:
            self.reboot_delayed(outlet, delay, duration)

    def on_off_immediate(self, outlet, on):
        (outlet, outlet_name) = self.get_outlet(outlet)

        self.control_outlet(outlet)

        if on:
            cmd = self.APC_IMMEDIATE_ON
            str_cmd = "On"
        else:
            cmd = self.APC_IMMEDIATE_OFF
            str_cmd = "Off"

        self.sendnl(cmd)
        self.sendnl(APC_YES)
        self.sendnl("")

        self.get_command_result()

        self.notify(outlet_name, str_cmd)

        self._escape_to_main()

    def on_off_delayed(self, outlet, on, delay):
        raise NotImplementedError()

    def on(self, outlet, delay):
        if delay == 0:
            self.on_off_immediate(outlet, True)
        else:
            self.on_off_delayed(outlet, True, delay)

    def off(self, outlet, delay):
        if delay == 0:
            self.on_off_immediate(outlet, False)
        else:
            self.on_off_delayed(outlet, False, delay)

    def debug(self):
        self.child.interact()

    def disconnect(self):
        # self._escape_to_main()

        self.sendnl(APC_LOGOUT)
        self.child.sendeof()
        if not self.quiet:
            print("DISCONNECTED from %s" % self.host)

        if self.verbose:
            print("[%s]" % "".join(self.child.readlines()))

        self.child.close()
        self.lock.unlock()

    def control_outlet(self, outlet):
        raise NotImplementedError()

    def get_command_result(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()


class APC2(AbstractAPC):
    APC_IMMEDIATE_ON = "1"
    APC_IMMEDIATE_OFF = "3"
    APC_IMMEDIATE_REBOOT = "4"

    def control_outlet(self, outlet):
        self.sendnl("1")
        self.sendnl("1")
        self.sendnl(str(outlet))
        self.sendnl("1")
        self.child.before

    def get_command_result(self):
        self.child.expect("Outlet State")


class APC3(AbstractAPC):
    APC_IMMEDIATE_ON = "1"
    APC_IMMEDIATE_OFF = "2"
    APC_IMMEDIATE_REBOOT = "3"
    APC_DELAYED_ON = "4"
    APC_DELAYED_OFF = "5"
    APC_DELAYED_REBOOT = "6"

    def control_outlet(self, outlet):
        self.sendnl("1")
        self.sendnl("2")
        self.sendnl("1")
        self.sendnl(str(outlet))
        if self.admin:
            self.sendnl("1")
        self.child.before

    def configure_outlet(self, outlet):
        self.sendnl("1")
        self.sendnl("2")
        self.sendnl("1")
        self.sendnl(str(outlet))
        if not self.admin:
            raise SystemExit(
                "Cannot configure an outlet if the user is not an administrator. Please use an Administrator account instead of an Outlet User."
            )
        self.child.before

    def get_command_result(self):
        self.child.expect("Command successfully issued")

    def set_power_delay(self, outlet, on, delay):
        self.configure_outlet(outlet)
        self.child.expect("Configure Outlet")
        if on:
            str_cmd = "On"
            self.sendnl("2")  # Power On Delay(sec)
        else:
            str_cmd = "Off"
            self.sendnl("3")  # Power Off Delay(sec)
        if delay == -1 or delay >= 0 and delay <= 7200:
            self.sendnl(str(delay))
        else:
            raise SystemExit(
                "Power %s Delay Range: -1 to 7200 sec, where -1=Never" % str_cmd
            )
        self.sendnl("5")  # Accept Changes
        self.child.before

    def on_off_delayed(self, outlet, on, delay):
        (outlet, outlet_name) = self.get_outlet(outlet)

        self.set_power_delay(outlet, on, delay)

        self._escape_to_main()

        self.control_outlet(outlet)
        self.child.expect("Control Outlet")

        if on:
            cmd = self.APC_DELAYED_ON
            str_cmd = "On"
        else:
            cmd = self.APC_DELAYED_OFF
            str_cmd = "Off"

        self.sendnl(cmd)
        self.sendnl(APC_YES)
        self.sendnl("")

        self.get_command_result()

        self.notify(outlet_name, "Delayed %s (%d s)" % (str_cmd, delay))

        self._escape_to_main()

    def status(self):
        self.sendnl("1")
        self.sendnl("2")
        self.sendnl("1")
        self.child.expect("-+ Outlet Control/Configuration -+")
        self.child.expect("<ESC>")
        s = self.child.before
        s = s.decode("utf-8")  # b'' -> string
        s = s.strip()
        rows = s.split("\n")
        lst_outlets = []
        for row in rows[:-1]:
            ol = Outlet.parse(row.strip())
            lst_outlets.append(ol)
        ol_collection = Outlets(lst_outlets)
        return ol_collection

    def set_reboot_duration(self, outlet, duration):
        self.configure_outlet(outlet)
        self.sendnl("4")  # Reboot Duration
        if duration < 5 or duration > 60:
            raise SystemExit("Reboot Duration Range: 5 to 60 sec")
        self.sendnl(str(duration))
        self.sendnl("5")  # Accept Changes

    def reboot_delayed(self, outlet, delay, duration):
        (outlet, outlet_name) = self.get_outlet(outlet)
        str_cmd = "reboot"
        self.set_reboot_duration(outlet, duration)
        self._escape_to_main()
        self.set_power_delay(outlet, False, delay)  # power off delay
        self._escape_to_main()
        self.set_power_delay(outlet, True, delay)  # power on delay
        self._escape_to_main()
        self.control_outlet(outlet)

        self.sendnl(self.APC_DELAYED_REBOOT)
        self.child.expect("Delayed Reboot")
        self.sendnl(APC_YES)
        self.sendnl("")

        self.get_command_result()

        self.notify(
            outlet_name,
            "Delayed %s (delay=%d duration=%d)" % (str_cmd, delay, duration),
        )

        self._escape_to_main()
