#!/usr/bin/env bash

# Force install Python 3.11
apt-get update
apt-get install -y python3.11 python3.11-dev python3.11-distutils

# Create symbolic link if needed
ln -sf /usr/bin/python3.11 /usr/bin/python3

# Install pip for Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install requirements
python3.11 -m pip install -r requirements.txt

# Install Playwright
python3.11 -m playwright install chromium
python3.11 -m playwright install-deps
