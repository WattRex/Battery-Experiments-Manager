#!/bin/bash
# This script is used to deploy the master node

cd "$(dirname "$0")/.."

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
required_file_list=("docker-compose.yml" "config_params.yaml" "web_server/.cred.env"
                    "web_server/log_config.yaml" "mn_manager/log_config.yaml"
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

