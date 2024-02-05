<h1> Battery Experiments Manager Installation guide </h1>

<h2> Structure and initialization </h2>
<p style="text-align: justify">
The application is divided in 3 containers: the web server, the database and the master node manager. The web server is based on the <a src="https://www.djangoproject.com/">Django framework</a>, which is a Python framework that allows to develop web applications following the MVC architecture. The database is based on <a src="https://www.mysql.com/">MySQL</a>, which is a relational database management system. Both services are deployed in <a src="https://www.docker.com/">Docker</a> containers, which have to be hosted in a server. The web server docker container uses a <a src="https://hub.docker.com/_/python">Python image pregenerated from docker hub</a>  as base to create the final image, adding: custom files, installing requirements, etc. The database docker container uses a <a src="https://hub.docker.com/_/mysql">MySQL image pregenerated from docker hub</a> and only a custom .sql script file to initialize the database but it is provided in the final steps. To deploy the images in container with Docker, it used a <a src="https://docs.docker.com/compose/compose-file/">docker-compose.yml</a> file, which is a file that allows to configure and run multiple containers. In this <code>docker-compose.yml</code> file is where the credentials of the database and web server are provided using a <code>.cred.env</code> file stored in the same folder as the <code>docker-compose.yml</code> file. The <code>.cred.env</code> file is not provided in this repository because it contains sensitive information and it has to be created by the user. The master node manager is a container that is used to manage the communication between web_server/database and the cycler software of each computational unit.
</p>
<h2> Instructions to deploy the application </h2>
<p style="padding-left:15px; text-align: justify">
 1. First of all, it is necessary to clone or download this repository in the server where the application will be deployed.
 <br/> 
 2. The repository has some files with the name example inside the folder devops and its´ subfolders. This files are examples and therefor there should be a file with the same name (withou _example).
 One of this files is the <code>.cred.env</code> file in the devops/master_db folder of the repository. The <code>.cred.env</code> file has to contain the credentials of the database and web server. The credentials of the database are the same as the ones used to connect to the database from the cycler software. The <code>.cred.env</code> file has to be written as follows:
 <br/>
 </p>
 <pre>
<code>
# MYSQL Environment variables used by the database container to create the database and user
MYSQL_DATABASE=wattrex_db       #Name of the database
MYSQL_USER=user                 #User of the database
MYSQL_PASSWORD=pass             #Password of the user of the database
MYSQL_ROOT_PASSWORD=toor        #Password of the root user of the database
default-character-set=utf8      #Character set of the database

#DJANGO DATABASE CONNECTION PARAMETERS (used by the web server and they have to be the same as the ones used by the cycler software and database)
DJANGO_DB1_database=wattrex_db  
DJANGO_DB1_user=user
DJANGO_DB1_password=pass
DJANGO_DB1_default-character-set=utf8   
DJANGO_DB1_host=192.168.0.88            #IP of the server where the database is hosted Usually the one where the app is been launched.
DJANGO_DB1_port=3369                    #Port of the database specified in the docker-compose.yml file
SECRET_KEY=eXaMpLe_SeCrEtKeY!           #Secret key used by Django to encrypt the data
</code>
</pre>
<p style="padding-left:15px; text-align: justify">
There must be another <code>.cred.env</code> inside the devops/broker_mqtt folder with the user and password of the rabbit service which is going to be used, with a structure as shown next:
</p>
<pre>
<code>
RABBITMQ_DEFAULT_USER=user
RABBITMQ_DEFAULT_PASS=pass
</code>
</pre>

<p style="padding-left:15px; text-align: justify">Other files that are necessary to deploy the application are the <code>.cred.yaml</code>, <code>log_config.yaml</code> and <code>config_params.yaml</code> files. The files <code>.cred.yaml</code> and <code>log_config.yaml</code> have to be stored inside the folder called mn_manager inside the devops folder. Both files are used inside the master node manager container. The <code>config_params.yaml</code> file has to be stored inside the devops folder. Those files have to be written as follows:
This file is the most important as it must have the same values written in the <code>.cred.env</code> files.<br/></p>
<code>.cred.yaml</code>
<pre>
<code>
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
</code>
</pre>

`log_config.yaml`
<pre>
<code>
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
</code>
</pre>

`config_params.yaml`
<pre>
<code>
---

system_shared_tool:
  DEFAULT_CHAN_NUM_MSG: 350
  DEFAULT_IPC_MSG_SIZE: 350
  DEFAULT_CHAN_TIMEOUT: 1
</code>
</pre>
<p style="padding-left:15px; text-align: justify">
3. Now it´s time to deploy the application, there are two ways for deploying it using the designated executable or manually with the docker commands. <br/>
  <p style="padding-left:25px; text-align: justify">
  <b>3.1. With the executable: </b><br/>
  To deploy with the executable, go to the root folder of the repository and execute:<br/>
  <code>
  ./devops/deploy.sh
  </code> 
  <br/>
  This will give you the option to deploy for developing or production, the main differences is that in production it will
  use the configuration for production and in develop it will use the development docker compose file. In order to build the images, it will be necessary to add the build argument.<br/>
  In this case, it is not necessary to deploy the broker of mqtt as it will do it automatically.<br/><br/>
  <b>3.2 Launching manually the application:</b>
  <p style="padding-left:30px; text-align: justify">
    <i>3.2.1</i> Before launching any service or application, it´s mandatory to export the variable CONFIG_FILE_PATH. <br/>
    <code>
    export CONFIG_FILE_PATH=~/absolute/path/to/config_params.yaml
    </code>
    <br/><br/>
    <i>3.2.2</i> Once all the files are created and before deploying the application, it is necessary to have access to some MQTT broker with the credentials specified in the `.cred.yaml` file. Otherwise, the master node manager container will not work properly. In case you need to deploy a broker execute the following command (using the docker compose plugin) while being in the devops/broker_mqtt folder: <br/>
    <code>docker compose up -d </code>
    <br>
    After this command you should see that a container named rabbit_mq has been deployed.<br/><br/>
    <i>3.2.3</i> If you already have any service running in the ports 8869 or 3369, you should change those ports in the `docker-compose.yml` file and update those changes in the credential files.
    After this previous steps, it is necessary to execute the following command (using the docker compose plugin) in the root folder of the repository to launch the containers, which will be the devops folder:<br/>
    <code>
    docker compose up -d
    </code><br/><br/>
    <i>3.2.4</i> When the containers are running for the first time, the database container will create a docker volume to store the data and will execute the `.sql script` file to create the database and user. Then, the web server will try to connect to the database but it will fail because the database is not ready yet. It is necessary to wait until the database is ready and then restart the web server container. To restart the web server container, it is necessary to execute the following command:<br/>
    <code>
    docker restart wattrex_web_server
    </code><br/><br/>
    <i>3.2.5</i> The master node manager container should be running at this point because it restarts until the database container is working properly. If it is not running when database and web are working, it is necessary to execute the following command:
    <code>
    docker restart wattrex_mn_manager
    </code>
    Now, the application should be running and it should be possible to access to it using the IP of the server and the port 8869.
    </p>
  </p>
</p>


<h2> STOP PROCESS </h2>
<p>
If you want to stop the containers, it can be done manually executing the following command in the root folder of the repository (where the <code>docker-compose.yml</code> file is located): <br/>
<code>
docker compose down
</code><br/>
Or being in the root folder of the repository, can execute the following command:<br/>
<code> ./devops/deploy.sh force-stop </code><br/>
When executing this command you will be ask if you were using the production or de developing app.

<h2> Useful arguments with the executable </h2>
<h3> build </h3>
<p>When using this command <code>./devops/deploy.sh build</code> the images will be build instead of using the ones downloaded </p>
<h3> mqtt </h3>
<p>This argument will launch the mqtt broker</p>
<h3> stop-mqtt </h3>
<p>This argument will stop the mqtt broker</p>
