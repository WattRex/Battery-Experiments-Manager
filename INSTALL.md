# Battery Experiments Manager Installation guide

## Structure and initialization
The application is divided in 3 containers: the web server, the database and the master node manager. The web server is based on the [Django framework](https://www.djangoproject.com/), which is a Python framework that allows to develop web applications following the MVC architecture. The database is based on [MySQL](https://www.mysql.com/), which is a relational database management system. Both services are deployed in [Docker](https://www.docker.com/) containers, which have to be hosted in a server. The web server docker container uses a [Python image pregenerated from docker hub](https://hub.docker.com/_/python) as base to create the final image, adding: custom files, installing requirements, etc. The database docker container uses a [MySQL image pregenerated from docker hub](https://hub.docker.com/_/mysql) and only a custom .sql script file to initialize the database but it is provided in the final steps. To deploy the images in container with Docker, it used a [docker-compose.yml](https://docs.docker.com/compose/compose-file/) file, which is a file that allows to configure and run multiple containers. In this `docker-compose.yml` file is where the credentials of the database and web server are provided using a `.cred.env` file stored in the same folder as the `docker-compose.yml` file. The `.cred.env` file is not provided in this repository because it contains sensitive information and it has to be created by the user. The master node manager is a container that is used to manage the communication between web_server/database and the cycler software of each computational unit.

## Instructions to deploy the application
 1. First of all, it is necessary to clone or download this repository in the server where the application will be deployed. 
 2. The repository has some files with the name example inside the folder devops and its´ subfolders. This files are examples and therefor there should be a file with the same name (withou _example).
 One of this files is the `.cred.env` file in the devops/master_db folder of the repository. The `.cred.env` file has to contain the credentials of the database and web server. The credentials of the database are the same as the ones used to connect to the database from the cycler software. The `.cred.env` file has to be written as follows:
```
# MYSQL Environment variables used by the database container to create the database and user
MYSQL_DATABASE=wattrex_db       #Name of the database
MYSQL_USER=user                 #User of the database
MYSQL_PASSWORD=pass             #Password of the user of the database
MYSQL_ROOT_PASSWORD=toor        #Password of the root user of the database
default-character-set=utf8      #Character set of the database

# DJANGO DATABASE CONNECTION PARAMETERS (used by the web server and they have to be the same as the ones used by the cycler software and database)
DJANGO_DB1_database=wattrex_db  
DJANGO_DB1_user=user
DJANGO_DB1_password=pass
DJANGO_DB1_default-character-set=utf8   
DJANGO_DB1_host=192.168.0.88            #IP of the server where the database is hosted Usually the one where the app is been launched.
DJANGO_DB1_port=3369                    #Port of the database specified in the docker-compose.yml file
SECRET_KEY=eXaMpLe_SeCrEtKeY!           #Secret key used by Django to encrypt the data
```

 There must be another `.cred.env` inside the devops/broker_mqtt folder with the user and password of the rabbit service which is going to be used, with a structure as shown next:
```
RABBITMQ_DEFAULT_USER=user
RABBITMQ_DEFAULT_PASS=pass
```

Other files that are necessary to deploy the application are the `.cred.yaml`, `log_config.yaml` and `config_params.yaml` files. The files `.cred.yaml` and `log_config.yaml` have to be stored inside the folder called mn_manager inside the devops folder. Both files are used inside the master node manager container. The `config_params.yaml` file has to be stored inside the devops folder. Those files have to be written as follows:
This file is the most important as it must have the same values written in the `.cred.env` files.
`.cred.yaml`
```
---

master_db:
  user: ?
  password: ?
  host: ?.?.?.?
  port: ?
  database: ?
  engine: mysql

mqtt:
  user: ?
  password: ?
  host: ?.?.?.?
  port: 1883
```

`log_config.yaml`
```
---
__main__: "INFO"

##### DEV ######
wattrex_mn_manager: "INFO"
wattrex_driver_mqtt: "INFO"
wattrex_driver_db: "INFO"

##### DRV ######
can_sniffer: "INFO"
scpi_sniffer: "INFO"
drv_flow: "INFO"

##### SYS #####
sys_abs.sys_conf: "ERROR"
system_logger_tool: "ERROR"
system_shared_tool: "ERROR"

file_handlers: {}
```

`config_params.yaml`
```
---

system_shared_tool:
  DEFAULT_CHAN_NUM_MSG: 350
  DEFAULT_IPC_MSG_SIZE: 350
  DEFAULT_CHAN_TIMEOUT: 1
```
3. Before launching any service or application, it´s mandatory to export the variable CONFIG_FILE_PATH.
```
export CONFIG_FILE_PATH=~/absolute/path/to/config_params.yaml
```
4. Once all the files are created and before deploying the application, it is necessary to have access to some MQTT broker with the credentials specified in the `.cred.yaml` file. Otherwise, the master node manager container will not work properly. In case you need to deploy a broker execute the following command (using the docker compose plugin) while being in the devops/broker_mqtt folder:
```
docker compose up -d
```
After this command you should see that a container named rabbit_mq has been deployed.

5. If you already have any service running in the ports 8869 or 3369, you should change those ports in the `docker-compose.yml` file and update those changes in the credential files.
After this previous steps, it is necessary to execute the following command (using the docker compose plugin) in the root folder of the repository to launch the containers, which will be the devops folder:
```
docker compose up -d
```
6. When the containers are running for the first time, the database container will create a docker volume to store the data and will execute the `.sql script` file to create the database and user. Then, the web server will try to connect to the database but it will fail because the database is not ready yet. It is necessary to wait until the database is ready and then restart the web server container. To restart the web server container, it is necessary to execute the following command:
```
docker restart wattrex_web_server
```
7. The master node manager container should be running at this point because it restarts until the database container is working properly. If it is not running when database and web are working, it is necessary to execute the following command:
```
docker restart wattrex_mn_manager
```
Now, the application should be running and it should be possible to access to it using the IP of the server and the port 8869.

## STOP PROCESS
If you want to stop the containers, you can execute the following command in the root folder of the repository (where the `docker-compose.yml` file is located):
```
docker compose down
```
