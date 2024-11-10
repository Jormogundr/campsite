"""
Generate a secret key that satisfies Heroku's secret key requirements. Use the output to set your SECRET_KEY env var.
"""

import os
import secrets

def generate_secret_key():
    return secrets.token_hex(32)

if __name__ == "__main__":
    print("Generated SECRET_KEY:")
    print(generate_secret_key())