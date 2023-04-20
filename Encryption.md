# How to encrypt a configuration file using Python

The code below is a Python script that encrypts a configuration file using the [cryptography library](https://cryptography.io/en/latest/) and a key stored in an environment variable. The configuration file is named `config.ini` and the encrypted file is named `encrypted_config.ini`. The script also prints a message when the encryption is done.

## Prerequisites

To run the code, you need to have:

- Python installed on your computer. You can download it from [here](https://www.python.org/downloads/).
- The cryptography library installed using pip:

```bash
pip install cryptography
```

- A configuration file named `config.ini` in the same directory as the script. The configuration file can contain any settings you want to encrypt, such as database credentials, API keys, etc.

## Steps

1. Generate a key for encryption and decryption using the Fernet module from the cryptography library. You can use the following code to generate a random key and save it in a file named `key.txt`:

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
with open("key.txt", "wb") as file:
    file.write(key)
```

2. Set an environment variable named `ENCRYPTION_KEY` with the value of the key you generated. You can use the following command in your terminal to do so:

```bash
export ENCRYPTION_KEY=$(cat key.txt)
```

3. Run the script using the following command in your terminal:

```bash
python encrypt_config_file.py
```

The script will read the `config.ini` file, encrypt its contents using the key from the environment variable, and write the encrypted data to `encrypted_config.ini` file. It will also print **"Configuration file encrypted successfully."** when done.

## Code

Here is the code of the script:

```python
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
```