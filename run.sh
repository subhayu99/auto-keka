#!/bin/bash

if grep -q -E 'KEKA_USERNAME|KEKA_PASSWORD|USER_LAT|USER_LNG' .env; then
    echo ".env file contains the required environment variables"
else
    echo ".env file does not contain the required environment variables. Filling it up now"
    
    read -p "Please enter your KEKA_USERNAME: " KEKA_USERNAME
    read -p "Please enter your KEKA_PASSWORD: " KEKA_PASSWORD
    read -p "Please enter your LATITUDE: " USER_LAT
    read -p "Please enter your LONGITUDE: " USER_LNG

    echo "KEKA_USERNAME=$KEKA_USERNAME" >> .env
    echo "KEKA_PASSWORD=$KEKA_PASSWORD" >> .env
    echo "USER_LAT=$USER_LAT" >> .env
    echo "USER_LNG=$USER_LNG" >> .env

    echo "Environment variables written to .env file"
fi

read -p "Do you want to start the backend? [y|N]: " runBackend

if [ "$runBackend" == "y" ]; then
    if ! command -v docker &> /dev/null; then
        echo "Docker could not be found"
        echo "visit this url (https://docs.docker.com/get-docker/) to install docker on your system"
        echo "Run this script once it is installed"
        exit
    fi

    sudo docker stop $(sudo docker ps -q -f ancestor=auto-keka) &> /dev/null
    sudo docker build -t auto-keka . --no-cache &> /dev/null
    sudo docker run -dp 5000:5000 auto-keka &> /dev/null
    echo "running auto-keka image with container id: $(sudo docker ps -q -f ancestor=auto-keka)"
    echo
    echo "visit http://0.0.0.0:5000/docs to see the api docs"
fi


read -p "Do you want to add cron job? [y|N]: " addCronJobs
if [ "$addCronJobs" == "y" ]; then
    echo "Adding cron job"
    crontab -l > mycron
    echo "0 10,19 * * 1-5 sleep $[($RANDOM % 1800) + 1]s && curl http://0.0.0.0/punch/" >> mycron
    crontab mycron
    rm mycron
    echo "Cron job added successfully for 10:00 AM and 7:00 PM every weekday"
fi