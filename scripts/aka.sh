#!/bin/bash

function usage() {
    echo "This script helps you manage and run the Auto Keka API."
    echo ""
    echo "Usage: ./aka [command]"
    echo ""
    echo "Commands:"
    echo "  start        Builds and runs the auto-keka container and sets up environment variables"
    echo "  reload       Reloads the auto-keka container"
    echo "  help         Show this help documentation"
    echo ""
    echo "Options:"
    echo "  - If no command is provided, the script will show the help documentation."
    echo "  - When the 'start' command is used, the script will check for the presence of required environment variables in the .env file. If the variables are not present, the script will prompt the user to enter them."
    echo "  - The 'start' command also gives the option to run the built-in scheduler."
    echo "  - The 'reload' command stops and restarts the auto-keka container."
}

if [ $# -eq 0 ] || ([ $# -eq 1 ] && [ $1 = "help" ]); then
    usage
    exit 0
fi

if [ $1 = "reload" ]; then
    echo "killing container $(sudo docker ps -q -f ancestor=auto-keka)"
    sudo docker stop $(sudo docker ps -q -f ancestor=auto-keka)
    sudo docker run -dp 5000:5000 -v $(pwd)/logs:/auto-keka/logs auto-keka
    echo "running auto-keka image with container id: $(sudo docker ps -q -f ancestor=auto-keka)"
    exit 0
fi

if [ $1 = "start" ]; then
    if grep -q -E 'KEKA_USERNAME|KEKA_PASSWORD|USER_LAT|USER_LNG' .env; then
        echo ".env file contains the required environment variables"
    else
        echo ".env file does not contain the required environment variables. Let's fill it now"

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

    if ! command -v docker &> /dev/null; then
        echo "Docker could not be found"
        echo "visit this url (https://docs.docker.com/get-docker/) to install docker on your system"
        echo "Run this script once it is installed"
        exit
    fi

    read -p "Do you want to run the built-in scheduler? [y|N]: " runScheduler
    if [ "$runScheduler" == "y" ]; then
        sed -i 's/^# nohup python3 schedule.py/nohup python3 schedule.py/g' scripts/startup.sh
    else
        sed -i 's/^nohup python3 schedule.py/# nohup python3 schedule.py/g' scripts/startup.sh
    fi

    echo "killing container $(sudo docker ps -q -f ancestor=auto-keka)"
    sudo docker stop $(sudo docker ps -q -f ancestor=auto-keka) # &> /dev/null
    sudo docker build -t auto-keka . --no-cache # &> /dev/null
    sudo docker run -dp 5000:5000 -v $(pwd)/logs:/auto-keka/logs auto-keka # &> /dev/null
    echo "running auto-keka image with container id: $(sudo docker ps -q -f ancestor=auto-keka)"
    echo
    echo "visit http://0.0.0.0:5000/docs to explore the api"
fi
