# picoWOL.py

picoWOL.py is a Python script that allows you to remotely wake up, shut down, or put to sleep a target PC using a Raspberry Pi Pico and GPIO input pins.

## Configuration

The script requires a configuration file named 'config.cfg' in the same directory as the script. The configuration file should contain the following information, one per line:

- ZeroTier network ID
- ZeroTier API key
- WiFi SSID
- WiFi password
- Target PC MAC address

Example configuration file:

```
0123456789abcdef
abcdefghijklmnopqrstuvwxyz0123456789abcdef
MyWiFiSSID
MyWiFiPassword
01:23:45:67:89:ab
```

## GPIO Input Pins

The script listens for input on the following GPIO pins:

- Pin 17: Shutdown
- Pin 18: Wake up
- Pin 19: Sleep

## Functions

The script contains the following functions:

- `reboot()`: Sends a Wake-on-LAN magic packet to the target PC.
- `shutdown()`: Sends a shutdown command to the target PC.
- `sleep()`: Sends a sleep command to the target PC.

## Dependencies

The script requires the following dependencies:

- RPi.GPIO
- zerotier
- cryptography

## Usage

To use the script, simply run it on a Raspberry Pi Pico connected to the target PC and GPIO input pins. The script will listen for input on the GPIO pins and perform the corresponding action when triggered.