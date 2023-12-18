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

#######################          PROJECT IMPORTS         #######################
from system_shared_tool import SysShdIpcChanC, SysShdNodeC, SysShdNodeStatusE
from wattrex_cycler_datatypes.comm_data import (CommDataCuC,CommDataRegisterTypeE,
                                                        CommDataHeartbeatC, CommDataDeviceC,
                                                        CommDataMnCmdDataC, CommDataMnCmdTypeE)

#######################          MODULE IMPORTS          #######################
from .mn_broker_client import BrokerClientC
from .mn_db_facade import DbFacadeC

#######################              ENUMS               #######################
MN_REQS_CHAN_NAME = 'mn_reqs'
MN_DATA_CHAN_NAME = 'mn_data'

#######################             CLASSES              #######################

class MnManagerNodeC(SysShdNodeC): # pylint: disable=abstract-method
    '''
    Cu Manager Class to instanciate a CU Manager Node
    '''
    def __init__(self, working_flag : threading.Event, cycle_period : int) -> None:
        '''
        Initialize the node.
        '''
        super().__init__(name='cu_manager_node', cycle_period=cycle_period,
                working_flag=working_flag)

        self.mn_req_chan : SysShdIpcChanC = SysShdIpcChanC(name=MN_REQS_CHAN_NAME,
                                                            max_message_size=350,
                                                            max_msg=350)
        self.mn_data_chan : SysShdIpcChanC = SysShdIpcChanC(name=MN_DATA_CHAN_NAME,
                                                            max_message_size=350,
                                                            max_msg=350)
        self.db_facha : DbFacadeC = DbFacadeC()
        avail_cus : List[int] = self.db_facha.get_available_cus()
        log.info(f"Already connected devices: {avail_cus}")

        self.client_mqtt : BrokerClientC = BrokerClientC(error_callback=self.error_cb,
                                                         register_cb=self.register_cb,
                                                         heartbeat_cb=self.heartbeat_cb,
                                                         inform_dev_cb=self.detect_devices_cb,
                                                         avail_cus=avail_cus)

    def error_cb(self, data) -> None:
        '''Error callback for Broker.

        Args:
            data ([type]): [description]
        '''
        log.critical(f'Error in Broker Client: {data}')
        self.status = SysShdNodeStatusE.COMM_ERROR


    def register_cb(self, cu_info : CommDataCuC) -> None:
        '''This callback is called when the CU is received.

        Args:
            cu_info (CommDataCuC): [description]
        '''
        if cu_info.msg_type is CommDataRegisterTypeE.DISCOVER:
            found_cu = self.db_facha.get_cu_by_mac(cu_info.mac)
            if found_cu is not None:
                cu_info.cu_id = found_cu
                cu_info.msg_type = CommDataRegisterTypeE.OFFER
                log.info(f"{cu_info.msg_type.name}s cu_id {cu_info.cu_id} for device already "
                        + "found in database with MAC:"
                        + f"{cu_info.mac}")
            else:
                new_cu_id = self.db_facha.get_last_cu_id()
                cu_info.cu_id = new_cu_id + 1
                cu_info.msg_type = CommDataRegisterTypeE.OFFER
                log.info(f"{cu_info.msg_type.name}s cu_id {cu_info.cu_id} for device with MAC:"
                        + f"{cu_info.mac}")
            self.client_mqtt.publish_inform(cu_info)
        elif cu_info.msg_type is CommDataRegisterTypeE.REQUEST:
            if self.db_facha.is_cu_registered(cu_info):
                cu_info.msg_type = CommDataRegisterTypeE.ACK
                log.info(f"Send {cu_info.msg_type.name}. Already registered CU: {cu_info.cu_id} "
                            + f"with MAC: {cu_info.mac}")
                self.client_mqtt.publish_inform(cu_info)
            else:
                self.db_facha.register_cu(cu_info)
                try:
                    self.db_facha.commit()
                except Exception as err:
                    log.error(f"Error on commiting new CU: {err}")
                else:
                    cu_info.msg_type = CommDataRegisterTypeE.ACK
                    log.info(f"Send {cu_info.msg_type.name}. Registered new CU: {cu_info.cu_id} "
                            + f"with MAC: {cu_info.mac}")
                    self.client_mqtt.publish_inform(cu_info)
        else:
            log.debug(f"Inconsistent register message: {cu_info.msg_type}. Ignore it.")


    def heartbeat_cb(self, heartbeat : CommDataHeartbeatC) -> None:
        '''Handle heartbeat data.

        Args:
            hb (CommDataHeartbeatC): [description]
        '''
        self.db_facha.update_heartbeat(heartbeat=heartbeat)


    def detect_devices_cb(self, cu_id : int, devices : List[CommDataDeviceC]) -> None:
        '''Callback called when a device is detected .

        Args:
            cu_id (int): [description]
            devices (List[CommDataDeviceC]): [description]
        '''
        log.info(f"Devices detected for [{cu_id}]: {devices}")
        self.db_facha.update_devices(cu_id, devices)
        msg_data = CommDataMnCmdDataC(cmd_type=CommDataMnCmdTypeE.INF_DEV,
                                            cu_id=cu_id, devices=devices)
        self.mn_data_chan.send_data(msg_data)


    def apply_cmds(self) -> None:
        '''Applies all registered commands to the broker.
        '''
        cmd = self.mn_req_chan.receive_data_unblocking()
        if isinstance(cmd, CommDataMnCmdDataC):
            log.warning(f"Applying {cmd.cmd_type.name} cmd")
            if cmd.cmd_type is CommDataMnCmdTypeE.LAUNCH:
                self.client_mqtt.publish_launch(cu_id=cmd.cu_id, cs_id=cmd.cs_id)
            elif cmd.cmd_type is CommDataMnCmdTypeE.REQ_DETECT:
                self.client_mqtt.publish_req_devices(cu_id=cmd.cu_id)


    def process_iteration(self) -> None:
        '''Perform a single iteration of the protocol.
        '''
        log.debug("New Processing iteration")
        self.apply_cmds()
        self.db_facha.track_avail_cu()
        self.db_facha.commit()
        self.client_mqtt.process_incomming_msg()


    def stop(self) -> None:
        '''Stop the stream .
        '''
        self.client_mqtt.close()

#######################            FUNCTIONS             #######################
