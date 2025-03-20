#!/bin/bash

# Install pip if missing
echo "Checking if pip is installed..."
python3 -m ensurepip --default-pip

# Install project dependencies
echo "Building the project..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt


# Apply migrations
echo "Make Migration..."
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

