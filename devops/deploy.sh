#!/bin/bash
# This script is used to deploy the master node

# CONSTANTS
MIN_MSG_MAX=300
MIN_MSGSIZE_MAX=8000

ARG1=$1

#Set production environment as default
docker_compose_file="docker-compose.yml"

cd "$(dirname "$0")/.."

initial_deploy () {
    # TODO: Add force_stop to restart the system if it is already running
    check_mqueue_sizes
    # If ARG1 is equal to "build", execute the build command
    if [ "${ARG1}" = "build" ]; then
        docker compose -f ./devops/${docker_compose_file} up -d --build
    else
        docker compose -f ./devops/${docker_compose_file} up -d
    fi
    if [ $? -eq 0 ]; then
        echo "Master node containers deployed"
        # Check if the master node database is running to reset the web container
        source ./devops/master_db/.cred.env &> /dev/null
        text_wait_db="Waiting for master db"
        is_db_up=0
        dots_counter=0
        echo ${text_wait_db}
        while [ $is_db_up -lt 15 ]
        do
            check_master_db
            if [ $? -eq 0 ]; then
                is_db_up=$((is_db_up+1))
            fi
            text_wait_db="${text_wait_db}."
            dots_counter=$((dots_counter+1))
            sleep 2
            echo -e '\e[1A\e[K'$text_wait_db
            if [ $dots_counter -eq 10 ]; then
                dots_counter=0
                text_wait_db="Waiting for master db"
            fi
        done
        docker restart wattrex_web_server

    else
        echo "Error deploying the master node"
        exit 1
    fi
}

check_mqueue_sizes () {
    # Check if the mqueue sizes are set over the minimum required
    error_mqueue_sizes=0

    # Perform the cat command and store the result in a variable
    result_msg_max=$(cat /proc/sys/fs/mqueue/msg_max)
    result_msgsize_max=$(cat /proc/sys/fs/mqueue/msgsize_max)

    # Check if the result is lower than 300
    if [ $result_msg_max -lt $MIN_MSG_MAX ]; then
        echo "Msg_max value (${result_msg_max}) is lower than the min required (${MIN_MSG_MAX})."
        error_mqueue_sizes=1
    fi
    if [ $result_msgsize_max -lt $MIN_MSGSIZE_MAX ]; then
        echo "Msgsize_max value (${result_msgsize_max}) is lower than the min required (${MIN_MSGSIZE_MAX})."
        error_mqueue_sizes=1
    fi

    # If there is an error, exit the script
    if [ $error_mqueue_sizes -eq 1 ]; then
        exit 1
    fi
}

check_master_db () {
    # Check if the master node database is running
    docker exec -it wattrex_master_db mysqladmin ping -u ${MYSQL_USER} -p${MYSQL_PASSWORD} &> /dev/null
}

launch_mqtt () {
    docker compose -f ./devops/broker_mqtt/docker-compose.yml up -d
}

stop_mqtt () {
    docker compose -f ./devops/broker_mqtt/docker-compose.yml down
}

ask_for_environment () {
    # Ask for input of dev or prod
    echo "Do you want to work with the dev or prod version? (dev/prod)"
    read -p "Type dev or prod: " dev_or_prod
    if [ "${dev_or_prod}" = "dev" ]; then
        docker_compose_file="dev-docker-compose.yml"
    elif [ "${dev_or_prod}" = "prod" ]; then
        docker_compose_file="docker-compose.yml"
    else
        echo "Invalid input"
        exit 1
    fi
}

################################################################################
#################################     MAIN     #################################
################################################################################

# Check if the required software is installed
if ! command -v docker &> /dev/null
then
    echo "Docker could not be found"
    exit 1
fi
if ! docker compose version &> /dev/null
then
    echo "Docker compose could not be found"
    exit 1
fi

# Check if the required files are present.
required_file_list=("docker-compose.yml" "dev-docker-compose.yml" "config_params.yaml"
                    "web_server/.cred.env" "web_server/log_config.yaml" "mn_manager/log_config.yaml"
                    "mn_manager/.cred.yaml" "master_db/.cred.env"
                    "master_db/createMasterCyclerTables.sql"
                    "master_db/insertDeviceInfoToMaster.sql" "broker_mqtt/.cred.env"
                    "broker_mqtt/docker-compose.yml"
                    "broker_mqtt/enabled_plugins")
for file in ${required_file_list}
do
    file_path=./devops/${file}
    if [ ! -f ${file_path} ]; then
    echo "${file_path} not found"
    exit 1
    fi
done

# Check command to run depending on the arguments
case ${ARG1} in
    ""|"build")
        # echo "Initial Deploy"
        launch_mqtt
        ask_for_environment
        initial_deploy
        ;;
    "mqtt")
        # echo "Launch MQTT"
        launch_mqtt
        ;;
    "stop-mqtt")
        # echo "Stop MQTT"
        stop_mqtt
        ;;
    "force-stop")
        # echo "Force Stop"
        stop_mqtt
        ask_for_environment
        docker compose -f ./devops/${docker_compose_file} down
        ;;
    *)
        >&2 echo "[ERROR] Invalid command type: ${ARG1}"
        exit 3
        ;;
esac

