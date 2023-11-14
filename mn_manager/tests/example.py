#!/usr/bin/python3
"""
Master Node that manages connections with the cu nodes.
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import time
import threading

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from wattrex_mn_manager import MnManagerNodeC, MN_REQS_CHAN_NAME

from wattrex_battery_cycler_datatypes.comm_data import (CommDataMnCmdDataC, CommDataMnCmdTypeE)

#######################          PROJECT IMPORTS         #######################
from system_shared_tool import SysShdIpcChanC

#######################              ENUMS               #######################


#######################             CLASSES              #######################


#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    mn_manager_node = MnManagerNodeC(working_flag=working_flag_event, cycle_period=1000)

    mn_manager_node.start()

    time.sleep(5)
    req_chan = SysShdIpcChanC(name=MN_REQS_CHAN_NAME)

    # Send launch command
    # cmd_launch = CommDataMnCmdDataC(cmd_type=CommDataMnCmdTypeE.LAUNCH, cu_id=5, cs_id=1)
    # log.warning(f"Sending launch cmd: {cmd_launch.cmd_type}")
    # req_chan.send_data(cmd_launch)

    # Send detect devices command
    cmd_launch = CommDataMnCmdDataC(cmd_type=CommDataMnCmdTypeE.REQ_DETECT, cu_id=5)
    log.warning(f"Sending req detect cmd: {cmd_launch.cmd_type}")
    req_chan.send_data(cmd_launch)

    mn_manager_node.join()
