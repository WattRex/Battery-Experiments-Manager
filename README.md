# Battery Experiments Manager

## Description
This repository contains the code of the Battery Experiments Manager, a web application that allows to manage the experiments of any battery cycling laboratory. It is developed in Python, using the Django framework, and it is based on the MVC architecture. It is also used a MySQL database to store the data. The application is deployed in a Docker container, which has to be hosted in a server.

## Main functionalities
The application is designed to be used by the laboratory staff, who can create new batteries and experiments, as well as visualize the data of the experiments in a graph. It is necessary to use some software to execute the queued created experiments and write its result data in the database. If this cycler software is different from [Battery-Cyclers-Controler](https://github.com/WattRex/Battery-Cyclers-Controler/), the obtained data could be prepared to be imported in the application as a new finished experiment. The application allows to export the data in a CSV file and to generate a local html report of the experiments. On going experiments can be monitored in real time.

### Monitor
The monitor is a page that allows to visualize the data of the on going experiments in real time. It is possible to select any of the cycler stations which are cycling a experiment (experiment status is 'RUNNING'). The data is updated, by default, every 5 seconds. The user can also select the time range of the data to be displayed (last 1, 5, 15, etc minutes). The data is displayed in a graph, which can be zoomed in and out, and retrieved . The user can also download the data in a CSV file. It is possible to know the instructions that the cycler is executing at that moment.

### Experiments
The experiments page shows a list of all the experiments that have been created displayed as table. The user can sort the experiments by any of the columns (ID, name, status, dates, etc). For each experiment, the user can generate a preview page of experiment's info and data, download a local html report or export the data in a CSV file. The user can also filter the experiments by selecting the technology, battery, cycler station or profile used in the experiment. It is also possible to search for some text in the name or description of the experiment.

### Add battery
The add battery page allows to create a new battery. The user has to select and write all the fields that define a battery depending on its selected technology. If the battery is created successfully, the user will be redirected to the experiment page to create a new experiment.

### Add experiment
The add experiment page allows to create a new experiment. The user has to select the technology, battery, cycler station and profile to be used in the experiment and write a name and description for it. The compatible profiles are loaded to be selected when user has specified the battery and cycler station for the experiment. The profile can also be written or uploaded by the user, and it is verified before the experiment is uploaded to database. If the experiment is created successfully, the user will be redirected to the monitor page.

### Import experiment
The import experiment page allows to import a new experiment from a CSV file. The user has to select the file and write a name and description for the experiment. The file is verified before the experiment is uploaded to database. If the experiment is created successfully, the user will be redirected to the experiments page.

## Structure and initialization
The application is divided in 3 containers: the web server, the database and the master node manager. The web server is based on the [Django framework](https://www.djangoproject.com/), which is a Python framework that allows to develop web applications following the MVC architecture. The database is based on [MySQL](https://www.mysql.com/), which is a relational database management system. Both services are deployed in [Docker](https://www.docker.com/) containers, which have to be hosted in a server. The web server docker container uses a [Python image pregenerated from docker hub](https://hub.docker.com/_/python) as base to create the final image, adding: custom files, installing requirements, etc. The database docker container uses a [MySQL image pregenerated from docker hub](https://hub.docker.com/_/mysql) and only a custom .sql script file to initialize the database but it is provided in the final steps. To deploy the images in container with Docker, it used a [docker-compose.yml](https://docs.docker.com/compose/compose-file/) file, which is a file that allows to configure and run multiple containers. In this `docker-compose.yml` file is where the credentials of the database and web server are provided using a `.cred.env` file stored in the same folder as the `docker-compose.yml` file. The `.cred.env` file is not provided in this repository because it contains sensitive information and it has to be created by the user. The master node manager is a container that is used to manage the communication between web_server/database and the cycler software of each computational unit.

## Instructions to deploy the application
First of all, it is necessary to clone or download this repository in the server where the application will be deployed. Then, it is necessary to create the `.cred.env` file in the devops folder of the repository. The `.cred.env` file has to contain the credentials of the database and web server. The credentials of the database are the same as the ones used to connect to the database from the cycler software. The `.cred.env` file has to be written as follows:
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
DJANGO_DB1_host=192.168.0.88            #IP of the server where the database is hosted
DJANGO_DB1_port=3369                    #Port of the database specified in the docker-compose.yml file
SECRET_KEY=eXaMpLe_SeCrEtKeY!           #Secret key used by Django to encrypt the data
```

Other files that are necessary to deploy the application are the `.cred.yaml`, `log_config.yaml` and `config_params.yaml` files. The files `.cred.yaml` and `log_config.yaml` have to be stored inside the folder called mn_manager inside the devops folder. Both files are used inside the master node manager container. The `config_params.yaml` file has to be stored inside the devops folder. Those files have to be written as follows:

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
Before deploying the application, it is necessary to have access to some MQTT broker with the credentials specified in the `.cred.yaml` file. Otherwise, the master node manager container will not work properly.

If you already have any service running in the ports 8869 or 3369, you should change those ports in the `docker-compose.yml` file and update those changes in the credential files.
After this previous steps, it is necessary to execute the following command (using the docker compose plugin) in the root folder of the repository to launch the containers:
```
docker compose up -d
```
When the containers are running for the first time, the database container will create a docker volume to store the data and will execute the `.sql script` file to create the database and user. Then, the web server will try to connect to the database but it will fail because the database is not ready yet. It is necessary to wait until the database is ready and then restart the web server container. To restart the web server container, it is necessary to execute the following command:
```
docker restart wattrex_web_server
```
The master node manager container should be running at this point because it restarts until the database container is working properly. If it is not running when database and web are working, it is necessary to execute the following command:
```
docker restart wattrex_mn_manager
```

Now, the application should be running and it should be possible to access to it using the IP of the server and the port 8869. If you want to stop the containers, you can execute the following command in the root folder of the repository (where the `docker-compose.yml` file is located):
```
docker compose down
```

## Development process
The main development steps of the application are described in the [django_docker_dev_process.md](./django_docker_dev_process.md) file. Be careful because **the file is not updated with the last changes of the application** and it represents the development process of the first version of the application.