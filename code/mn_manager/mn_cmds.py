#!/usr/bin/python3
"""
Master Node that manages connections with the cu nodes.
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from enum import Enum

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################

#######################              ENUMS               #######################
class MnCmdTypeE(Enum):
    LAUNCH = 1
    INF_DEV = 2
    REQ_DETECT = 3

#######################             CLASSES              #######################
class MnCmdDataC:

    def __init__(self, cmd_type : MnCmdTypeE, cu_id : int, **kwargs) -> None:
        if isinstance(cmd_type, MnCmdTypeE):
            self.cmd_type = cmd_type
            self.cu_id = cu_id
            if cmd_type is MnCmdTypeE.LAUNCH:
                if 'cs_id' in kwargs:
                    self.cs_id = kwargs['cs_id']
                else:
                    raise ValueError('Missing argument cs_id')
            elif cmd_type is MnCmdTypeE.INF_DEV:
                if 'devices' in kwargs:
                    self.devices = kwargs['devices']
                else:
                    raise ValueError('Missing argument devices')
        else:
            raise TypeError(f'cmd_type must be of type MnCmdTypeE, not {type(cmd_type)}')

#######################            FUNCTIONS             #######################
