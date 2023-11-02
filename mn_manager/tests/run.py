#!/usr/bin/python3
"""
Run script for Master Node manager.
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import threading

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from wattrex_mn_manager import MnManagerNodeC

#######################          PROJECT IMPORTS         #######################


#######################              ENUMS               #######################


#######################             CLASSES              #######################


#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    mn_manager_node = MnManagerNodeC(working_flag=working_flag_event, cycle_period=1000)
    log.info("Running MN Manager Node...")
    mn_manager_node.run()
