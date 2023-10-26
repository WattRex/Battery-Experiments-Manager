#!/usr/bin/python3
"""
Master Node that manages connections with the cu nodes.
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
import threading
from typing import List

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='./log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################
from mn_broker_client import BrokerClientC
from mn_cmds import MnCmdDataC, MnCmdTypeE
from mn_db_facade import DbFacadeC

from wattrex_battery_cycler_datatypes.comm_data import CommDataCuC,\
    CommDataRegisterTypeE, CommDataHeartbeatC, CommDataDeviceC

#######################          PROJECT IMPORTS         #######################
from system_shared_tool import SysShdIpcChanC, SysShdNodeC

#######################              ENUMS               #######################
_MN_REQS_CHAN_NAME = 'mn_reqs'
_MN_DATA_CHAN_NAME = 'mn_data'
#######################             CLASSES              #######################

class MnManagerNodeC(SysShdNodeC):
    '''
    Cu Manager Class to instanciate a CU Manager Node
    '''
    def __init__(self, working_flag : threading.Event, cycle_period : int) -> None:
        '''
        Initialize the node.
        '''
        super().__init__(name='cu_manager_node', cycle_period=cycle_period,
                working_flag=working_flag)

        self.mn_req_chan : SysShdIpcChanC = SysShdIpcChanC(name=_MN_REQS_CHAN_NAME)
        self.mn_data_chan : SysShdIpcChanC = SysShdIpcChanC(name=_MN_DATA_CHAN_NAME)
        self.db_fach : DbFacadeC = DbFacadeC()
        avail_cus : List[int] = self.db_fach.get_available_cus()
        log.info(f"Already connected devices: {avail_cus}")

        self.client_mqtt : BrokerClientC = BrokerClientC(error_callback=self.error_cb,
                                                         register_cb=self.register_cb,
                                                         heartbeat_cb=self.heartbeat_cb,
                                                         inform_dev_cb=self.detect_devices_cb,
                                                         avail_cus=avail_cus)

    def error_cb(self, data) -> None:
        log.critical(f'Error in Broker Client: {data}')


    def register_cb(self, cu_info : CommDataCuC) -> None:
        if cu_info.msg_type is CommDataRegisterTypeE.DISCOVER:
            new_cu_id = self.db_fach.get_last_cu_id()
            # TODO: Check if the same device with the same MAC is already registered
            cu_info.cu_id = new_cu_id + 1
            cu_info.msg_type = CommDataRegisterTypeE.OFFER
            log.info(f"{cu_info.msg_type.name}s cu_id {cu_info.cu_id} for device with MAC: {cu_info.mac}")
            self.client_mqtt.publish_inform(cu_info)
        elif cu_info.msg_type is CommDataRegisterTypeE.REQUEST:
            self.db_fach.register_cu(cu_info)
            cu_info.msg_type = CommDataRegisterTypeE.ACK
            log.info(f"Send {cu_info.msg_type.name}. Registered new CU: {cu_info.cu_id} with MAC: {cu_info.mac}")
            self.client_mqtt.publish_inform(cu_info)
        else:
            log.debug(f"Inconsistent register message: {cu_info.msg_type}. Ignore it.")


    def heartbeat_cb(self, hb : CommDataHeartbeatC) -> None:
        self.db_fach.update_heartbeat(hb)


    def detect_devices_cb(self, cu_id : int, devices : List[CommDataDeviceC]) -> None:
        log.info(f"Devices detected for [{cu_id}]: {devices}")
        self.db_fach.update_devices(cu_id, devices)
        msg_data = MnCmdDataC(cmd_type=MnCmdTypeE.INF_DEV, cu_id=cu_id, devices=devices)
        self.mn_data_chan.send_data(msg_data)


    def apply_cmds(self) -> None:
        cmd = self.mn_req_chan.receive_data_unblocking()
        if isinstance(cmd, MnCmdDataC):
            log.warning(f"Applying {cmd.cmd_type.name} cmd")
            if cmd.cmd_type is MnCmdTypeE.LAUNCH:
                self.client_mqtt.publish_launch(cu_id=cmd.cu_id, cs_id=cmd.cs_id)
            elif cmd.cmd_type is MnCmdTypeE.REQ_DETECT:
                self.client_mqtt.publish_req_devices(cu_id=cmd.cu_id)


    def process_iteration(self) -> None:
        self.apply_cmds()
        self.db_fach.commit()
        self.client_mqtt.process_incomming_msg()

#######################            FUNCTIONS             #######################

if __name__ == '__main__':
    working_flag_event : threading.Event = threading.Event()
    working_flag_event.set()
    cu_manager_node = MnManagerNodeC(working_flag=working_flag_event, cycle_period=1000)

    # cu_manager_node.run() # uncomment it for production code
    # TODO: production code must be until there, move al this code below to a example file

    cu_manager_node.start()
    import time
    time.sleep(5)
    req_chan = SysShdIpcChanC(name=_MN_REQS_CHAN_NAME)

    # Send launch command
    # cmd_launch = MnCmdDataC(cmd_type=MnCmdTypeE.LAUNCH, cu_id=5, cs_id=1)
    # log.warning(f"Sending launch cmd: {cmd_launch.cmd_type}")
    # req_chan.send_data(cmd_launch)


    # Send detect devices command
    cmd_launch = MnCmdDataC(cmd_type=MnCmdTypeE.REQ_DETECT, cu_id=5)
    log.warning(f"Sending req detect cmd: {cmd_launch.cmd_type}")
    req_chan.send_data(cmd_launch)

    cu_manager_node.join()
