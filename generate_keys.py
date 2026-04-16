import os
import secrets
from cryptography.fernet import Fernet

def generate_keys():
    secret_key = secrets.token_hex(32)
    encryption_key = Fernet.generate_key().decode()
    
    print(f"SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")

if __name__ == "__main__":
    generate_keys()
