import os
from cryptography.fernet import Fernet

# Load encryption key from environment variable
key = os.environ.get("ENCRYPTION_KEY").encode()

# Load configuration file contents
with open("config.ini", "rb") as file:
    config_data = file.read()

# Encrypt configuration file contents
fernet = Fernet(key)
encrypted_data = fernet.encrypt(config_data)

# Write encrypted configuration file
with open("encrypted_config.ini", "wb") as file:
    file.write(encrypted_data)

print("Configuration file encrypted successfully.")
