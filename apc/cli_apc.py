#!/usr/bin/env python

from argparse import ArgumentParser
import pexpect
from apc import APC
from apc import APC_DEFAULT_HOST, APC_DEFAULT_USER, APC_DEFAULT_PASSWORD


def main():
    parser = ArgumentParser(description="APC Python CLI")
    parser.add_argument(
        "--host", action="store", default=APC_DEFAULT_HOST, help="Override the host"
    )
    parser.add_argument(
        "--user", action="store", default=APC_DEFAULT_USER, help="Override the username"
    )
    parser.add_argument(
        "--password",
        action="store",
        default=APC_DEFAULT_PASSWORD,
        help="Override the password",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose messages")
    parser.add_argument("--quiet", action="store_true", help="Quiet")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument(
        "--reboot", action="store", metavar="OUTLET", help="Reboot an outlet"
    )
    parser.add_argument(
        "--off", action="store", metavar="OUTLET", help="Turn off an outlet"
    )
    parser.add_argument(
        "--on", action="store", metavar="OUTLET", help="Turn on an outlet"
    )
    parser.add_argument(
        "--cli",
        action="store",
        default="",
        help="command line to execute 'ssh {user}@{host}' or 'telnet {host}",
    )
    parser.add_argument(
        "--delay",
        action="store",
        default=0,
        help="delay before on/off (-1 to 7200 sec, where -1=Never)",
    )
    parser.add_argument(
        "--duration", action="store", default=5, help="reboot duration (5 to 60 sec)"
    )
    parser.add_argument("--status", action="store_true", help="Status of outlets")

    args = parser.parse_args()

    is_command_specified = (
        args.reboot or args.debug or args.on or args.off or args.status
    )

    if not is_command_specified:
        parser.print_usage()
        raise SystemExit(1)

    try:
        apc = APC(
            args.host, args.user, args.password, args.verbose, args.quiet, args.cli
        )
    except pexpect.TIMEOUT:
        raise SystemExit("ERROR: Timeout connecting to APC")

    args.delay = int(args.delay)
    args.duration = int(args.duration)

    if args.debug:
        apc.debug()
    else:
        try:
            if args.reboot:
                apc.reboot(args.reboot, args.delay, args.duration)
            elif args.on:
                apc.on(args.on, args.delay)
            elif args.off:
                apc.off(args.off, args.delay)
            elif args.status:
                print(apc.status())
        except pexpect.TIMEOUT as e:
            raise SystemExit("APC failed!  Pexpect result:\n%s" % e)
        finally:
            apc.disconnect()


if __name__ == "__main__":
    main()
