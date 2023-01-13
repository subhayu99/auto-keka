#!/bin/bash

if [ -f .env ]; then
    echo ".env file exists"
else
    echo ".env file does not exist"
    
    read -p "Please enter your KEKA_USERNAME: " KEKA_USERNAME
    read -p "Please enter your KEKA_PASSWORD: " KEKA_PASSWORD
    read -p "Please enter your LATITUDE: " USER_LAT
    read -p "Please enter your LONGITUDE: " USER_LNG
    read -p "Please enter your DETA_PROJECT_KEY: " DETA_PROJECT_KEY

    echo "KEKA_USERNAME=$KEKA_USERNAME" >> .env
    echo "KEKA_PASSWORD=$KEKA_PASSWORD" >> .env
    echo "USER_LAT=$USER_LAT" >> .env
    echo "USER_LNG=$USER_LNG" >> .env
    echo "DETA_PROJECT_KEY=$DETA_PROJECT_KEY" >> .env

    echo "Environment variables written to .env file"
fi

read -p "Do you want to start the backend? [y|N]: " runBackend

if [ "$runBackend" == "y" ]; then
    if ! command -v docker &> /dev/null
    then
        echo "Docker could not be found"
        echo "visit this url (https://docs.docker.com/get-docker/) to install docker on your system"
        echo "Run this script once it is installed"
        exit
    fi

    sudo docker stop $(sudo docker ps -q -f ancestor=auto-keka)
    sudo docker build -t auto-keka . --no-cache
    sudo docker run -dp 5000:5000 auto-keka
    echo "running auto-keka image with container id: $(sudo docker ps -q -f ancestor=auto-keka)"
    echo
    echo "visit http://0.0.0.0:5000/docs to see the api docs"
fi
