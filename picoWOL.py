import RPi.GPIO as GPIO
import zerotier
import time
import logging
import os
from cryptography.fernet import Fernet

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up GPIO input
GPIO.setmode(GPIO.BOARD)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Load encrypted configuration file
with open('config.cfg', 'rb') as file:
    config_data = file.read()

# Decrypt configuration file
key = os.environ.get("CONFIG_KEY")
cipher_suite = Fernet(key.encode())
config = cipher_suite.decrypt(config_data)

# Parse configuration data
config_lines = config.decode().split('\n')
zerotier_network_id = config_lines[0].strip()
zerotier_api_key = config_lines[1].strip()
wifi_ssid = config_lines[2].strip()
wifi_password = config_lines[3].strip()
target_pc_mac = config_lines[4].strip()

# Connect to ZeroTier network
zt = zerotier.Client()
zt.set_auth_header(f"Bearer {zerotier_api_key}")

# Define target PC IP address on ZeroTier network
zt_member = zt.get_member(zerotier_network_id, target_pc_mac)
target_pc_ip = zt_member.config.ipAssignments[0]

def reboot():
    try:
        # Send WOL magic packet to target PC
        os.system(f"wakeonlan {target_pc_mac}")
        logging.info("WOL magic packet sent to target PC")
    except Exception as e:
        logging.error(f"Failed to send WOL magic packet: {e}")

def shutdown():
    try:
        # Send shutdown command to target PC
        os.system(f"ssh pi@{target_pc_ip} 'sudo shutdown now'")
        logging.info("Shutdown command sent to target PC")
    except Exception as e:
        logging.error(f"Failed to send shutdown command: {e}")

def sleep():
    try:
        # Send sleep command to target PC
        os.system(f"ssh pi@{target_pc_ip} 'sudo systemctl suspend'")
        logging.info("Sleep command sent to target PC")
    except Exception as e:
        logging.error(f"Failed to send sleep command: {e}")

# Connect to WiFi network
os.system(f"sudo nmcli device wifi connect '{wifi_ssid}' password '{wifi_password}'")

while True:
    # Listen for GPIO input on pin 17
    if GPIO.input(17) == GPIO.HIGH:
        shutdown()
        break
    
    # Listen for GPIO input on pin 18
    if GPIO.input(18) == GPIO.HIGH:
        reboot()
        break
    
    # Listen for GPIO input on pin 19
    if GPIO.input(19) == GPIO.HIGH:
        sleep()
        break
    
    # Wait for 0.1 seconds before checking GPIO input again
    time.sleep(0.1)

# Clean up GPIO
GPIO.cleanup()
