"""Checks for any connected microbits and reads the serial port for output."""

from subprocess import Popen, PIPE
from pty import openpty
import os
import sys

SPECIAL_PRINT_CONDITIONS = {
    'clear': lambda: os.system('clear'),
    '/red\r\n': lambda: print('\033[31m', end=''),
    '/green\r\n': lambda: print('\033[32m', end=''),
    '/yellow\r\n': lambda: print('\033[33m', end=''),
    '/blue\r\n': lambda: print('\033[34m', end=''),
    '/pink\r\n': lambda: print('\033[95m', end=''),
    '/default\r\n': lambda: print('\033[0m', end=''),
    'lalala': lambda: print('yay')
    }

'''
https://unix.stackexchange.com/questions/42376/reading-from-serial-from-linux-command-line
'''

def read_device(DEVICE_NAME_IDENTIFIER, BAUDRATE):
    '''Start reading connected device output

    This is the proper way to start reading from a device
    checks are done to verify there is a connected device and no other programs are using the port

    Args:
        DEVICE_NAME_IDENTIFIER (str): name of connected device
        BAUDRATE (int): read at the selected baudrate
    Returns:
        None
    '''
    if os.name != "posix":
        raise BaseException("only works with posix")

    devices = get_connected_devices()
    # as iterator
    connected_microbits = filter(lambda device: device.startswith(DEVICE_NAME_IDENTIFIER), devices)
    # as list
    connected_microbits = list(connected_microbits)
    if len(connected_microbits) == 0:
        raise ValueError("no ports with the given name found")
    elif len(connected_microbits) != 1:
        # only allow one
        raise ValueError("more than one port with the same name was detected")
    for device in connected_microbits:
        print(device)
    connected_device = connected_microbits[0]
    serial_in_use(connected_device)

    __read_serial_data__(connected_device, BAUDRATE)
def __read_serial_data__(port_name: str, baudrate: int):
    """Start read of serial port.

    Open a pseudo-terminal and cat a port

    Args:
        port_name (str): name of connected port
        baudrate (int): read at the selected baudrate
    Returns:
        None
    """
    (master, slave) = openpty()
    # https://stackoverflow.com/questions/803265/getting-realtime-output-using-subprocess
    command = "(stty speed {} >/dev/null && cat) <{}".format(baudrate, port_name)
    command = ['sh', '-c', command]

    p = Popen(command, stdin=slave, stdout=PIPE, bufsize=-1,
               universal_newlines=None, shell=False)
    print("Start read")
    for line in p.stdout:
        str_line = line.decode('utf-8') # recieved in bytes so decode
        if SPECIAL_PRINT_CONDITIONS.get(str_line):
            SPECIAL_PRINT_CONDITIONS.get(str_line)()
        else:
            print(line)

def serial_in_use(device_name: str):
    """Print warning if serial port is in use.

    Check if any other programs are reading from serial port
    other programs reading at the same time could make output glitchy
    """
    command = "lsof -n -b | grep -c '{}'".format(device_name)
    process = Popen([command], shell=True, stdout=PIPE, preexec_fn=os.setsid)
    stdout, stderr = process.communicate()
    result = int(stdout.decode())
    if result >= 1:
        print("WARNING: another program is reading from the same port")


def get_connected_devices():
    """Return list of connected devices.

    Uses subprocess with shell to get a list of open ports

    Args:
        None
    Returns:
        list of devices
    """
    process = Popen(["ls /dev/cu.*"], shell=True, stdout=PIPE)
    stdout, stderr = process.communicate()
    devices = stdout.decode().split("\n")
    devices.pop()  # leaves trailing newline character which causes empty devices element
    return devices

def setup():
    selected_device=None
    selected_baudrate=None
    while selected_device == None:
        connected_devices = get_connected_devices()
        print("Pick a connected device:")
        for i, device in enumerate(connected_devices):
            print(str(i) + ". " + device)
        input_num=input("")
        if not input_num.isdigit():
            print("input must be positive integer")
            continue
        if int(input_num)+1>len(connected_devices):
            print("input not in range")
            continue
        selected_device=connected_devices[int(input_num)]
    while selected_baudrate == None:
        print("Pick a baudrate:")
        input_num=input("")
        if not input_num.isdigit():
            print("input must be positive integer")
            continue
        selected_baudrate=input_num
    read_device(selected_device, selected_baudrate)
        

if sys.stdin.isatty() and __name__ == "__main__":
    # is running through a tty and is not an imported module
    if len(sys.argv) >= 3:
        # run through command line with parameters
        read_device(sys.argv[1], sys.argv[2])
    else:
        setup()
            

