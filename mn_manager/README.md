# Master Node Manager

This module defines classes and methods to manage the master node. 
It communicates the web server and the database with the computational units.

# REQUIREMENTS

At the same file system level like this README.md file, 2 extra files have to be placed.

## .cred.yaml
Template:
```
---

database:
  user: ?
  password: ?
  host: ?.?.?.?
  port: ?
  database: wattrex_master_db
  engine: mysql

mqtt:
  user: ?
  password: ?
  host: ?.?.?.?
  port: ?
```

## log_config.yaml
With example content:
```
---
#YAML FILE START

__main__: "INFO"

##### DEV ######
mn_broker_client: "INFO"
mn_manager_node: "DEBUG"

##### DRV ######
drv_mqtt: "INFO"

##### SYS #####
system_logger_tool: "ERROR"
system_shared_tool: "ERROR"

file_handlers: {}
```