# cycler-web-server

```
# Install server
    $ mkdir serverWebCiclados
    $ cd serverWebCiclados
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install Django
```

```
# Install MySQL Connector / Python
    $ pip install mysql-connector-python
```

```
# Install mySql client (don't install it if you will use MySQL Connector / Python)
    $ sudo apt-get install default-libmysqlclient-dev
    $ pip install mysqlclient
```

```
# Create project
    $ django-admin startproject projecto_ciclados
    
    $ mv projecto_ciclados/manage.py ./
    $ mv projecto_ciclados/projecto_ciclados/* projecto_ciclados
    $ rm -r projecto_ciclados/projecto_ciclados/
```

```
# Run server
    $ python manage.py runserver
```

```
# Install Bootstrap 4.6.1
    $ pip install django-bootstrap4
    
    
# Add bootstrap to the INSTALLED_APPS in settings.py
    
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'bootstrap4', # <--- HERE
        'example',
    ]
    
# This way gives you connection with the online Bootstrap location (Bootstrap, JavaScript and JQuery)
```

```
# If you want to use bootstrap without Internet conexion...

    1º Open venv/lib/python3.9/site-packages/bootstrap4/bootstrap.py
    2º Check every version of the linked elements
    3º Download from the official repositories the same version
        (Bootstrap 4.6.1, with its own javascript, and jquery-3.5.1 .min.js and .slim.min.js)
    4º Create a folder called 'static' in the server's root folder and unzip all the bootstrap content there.
    5º Add the following code in the settings.py
        STATIC_URL = 'static/'

        STATICFILES_DIRS = [
            BASE_DIR / 'static',
        ]
    6º Now, in the bootstrap.py file, replace the urls to the online version by the local path of each element,
        and delete the 2 other fields.
    7º Add the following code to every html template where you want to use bootstrap
        <head>
            {% load bootstrap4 %}
            {% load bootstrap4 %}
        </head> 
        <body>
            
            {# At the body end #}
            {% bootstrap_javascript jquery='full' %}
        </body>
```

```
# Create django app
    $ python manage.py startapp auto_lab
```



Once you’ve created the app... [Configure it in the project](https://realpython.com/get-started-with-django-1/#create-a-django-application "Configure app in the project")


To create a docker image, you have to create in the main server folder, a file named Dockerfile. Write the next code in Dockerfile:
```
FROM python:3.9-alpine
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD ../serverWebCiclados/requirements2.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements2.txt
ADD ../serverWebCiclados /code/
EXPOSE 8000/tcp
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```
After that, to generate the docker image, you have to insert the following instruction (being in the same folder as the folder where Dockerfile is):
```
docker build -t cycling-web-server:0.0.2 .
```
**docker build** -> execute the creation of the image<br>
**-t** -> give a custom name to the image<br>
**cycling-web-server:0.0.2** -> custom given name<br>
**.** -> use the Dockerfile, created which is in the same folder, to generate the image with the desired files, installs and configurations.<br>

# Missing files:

## .cred.env

The path where those files have to be located is: `./batteryCycling_project/.cred......`
Inside them, a database conexion parameters and credentials have to be stored like the following example:
```
[client]
database = ???
user = ???
password = ???
host = ???
port = ???
default-character-set = utf8
```
