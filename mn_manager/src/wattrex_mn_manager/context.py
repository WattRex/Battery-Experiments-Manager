#!/usr/bin/python3
'''
This module manages the constants variables.
Those variables are used in the scripts inside the module and can be modified
in a config yaml file specified in the environment variable with name declared
in system_config_tool.
'''

#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
#######################         GENERIC IMPORTS          #######################

#######################      SYSTEM ABSTRACTION IMPORTS  #######################
from system_logger_tool import Logger, sys_log_logger_get_module_logger
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################       THIRD PARTY IMPORTS        #######################

#######################          PROJECT IMPORTS         #######################
from system_config_tool import sys_conf_update_config_params

#######################          MODULE IMPORTS          #######################

######################             CONSTANTS              ######################
# For further information check out README.md
DEFAULT_CRED_FILEPATH : str = 'devops/mn_manager/.cred.yaml' # Max number of allowed message per chan
DEFAULT_MN_NODE_NAME: str = 'cu_manager_node'
DEFAULT_NODE_PERIOD: int = 750 # ms # Period of the node
DEFAULT_TIMEOUT_BETWEEN_CONNECTIONS: int =15


CONSTANTS_NAMES = ('DEFAULT_CRED_FILEPATH','DEFAULT_MN_NODE_NAME', 'DEFAULT_NODE_PERIOD',
                    'DEFAULT_TIMEOUT_BETWEEN_CONNECTIONS')
sys_conf_update_config_params(context=globals(),
                              constants_names=CONSTANTS_NAMES)
