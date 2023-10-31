#!/usr/bin/python3
"""
Wrapper for the MQTT client
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import Callable, List
from pickle import dumps, loads

#######################       THIRD PARTY IMPORTS        #######################

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

from wattrex_battery_cycler_datatypes.comm_data import CommDataDeviceC

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='../log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.comm_data import CommDataCuC, CommDataRegisterTypeE,\
    CommDataHeartbeatC
from wattrex_driver_mqtt import DrvMqttDriverC

#######################              ENUMS               #######################
_REGISTER_TOPIC = '/register'
_INFORM_TOPIC = '/inform_reg'
_SUFFIX_RX_DET_DEV = '/detected_dev'
_SUFFIX_RX_HB = '/heartbeat'
_SUFFIX_TX_DET = '/req_detect'
_SUFFIX_TX_LAUNCH = '/launch'

#######################             CLASSES              #######################

class BrokerClientC():
    """
    Broker Client Class to instanciate a Broker Client object
    """
    def __init__(self, error_callback : Callable,
                 register_cb : Callable, heartbeat_cb : Callable,
                 inform_dev_cb : Callable, avail_cus : List[int]) -> None:

        self.mqtt : DrvMqttDriverC = DrvMqttDriverC(error_callback=error_callback,
                                                    cred_path='.cred.yaml')

        self.__register_cb : Callable = register_cb
        self.__heartbeat_cb : Callable = heartbeat_cb
        self.__inform_dev_cb : Callable = inform_dev_cb
        self.mqtt.subscribe(topic=_REGISTER_TOPIC, callback=self.process_register)
        self.mqtt.subscribe(topic=_INFORM_TOPIC, callback=self.process_register)
        for cu_id in avail_cus:
            self.__subscribe_cu(cu_id)


    def __subscribe_cu(self, cu_id : int) -> None:
        hb_topic = f'/{cu_id}{_SUFFIX_RX_HB}'
        self.mqtt.subscribe(topic=hb_topic, callback=self.process_heartbeat)
        det_dev_topic = f'/{cu_id}{_SUFFIX_RX_DET_DEV}'
        self.mqtt.subscribe(topic=det_dev_topic, callback=self.process_det_dev)


    def process_register(self, raw_data : bytearray) -> None:
        cu_info = loads(raw_data)
        if isinstance(cu_info, CommDataCuC):
            log.info(f'Received register cmd: {cu_info.msg_type}')
            self.__register_cb(cu_info)
        else:
            log.error(f'Invalid data received: {type(cu_info)}: {cu_info}')


    def process_heartbeat(self, raw_data : bytearray) -> None:
        hb : CommDataHeartbeatC = loads(raw_data)
        log.debug(f'Heartbeat received from: {hb.cu_id}')
        self.__heartbeat_cb(hb)


    def process_det_dev(self, raw_data : bytearray) -> None:
        # TODO: add cu_id to the message
        devices : List[CommDataDeviceC] = loads(raw_data)
        if len(devices) > 0:
            cu_id = devices[0].cu_id
            log.info(f"Received detected from [{cu_id}]")
            self.__inform_dev_cb(cu_id, devices)
        else:
            log.warning(f"No devices detected from any CU")

    def publish_inform(self, cu_info : CommDataCuC) -> None:
        if cu_info.msg_type is CommDataRegisterTypeE.ACK:
            self.__subscribe_cu(cu_info.cu_id)

        raw_cu = dumps(cu_info)
        self.mqtt.publish(topic=_INFORM_TOPIC, data=raw_cu)


    def publish_launch(self, cu_id : int, cs_id : int) -> None:
        launch_topic = f'/{cu_id}{_SUFFIX_TX_LAUNCH}'
        self.mqtt.publish(topic=launch_topic, data=cs_id)


    def publish_req_devices(self, cu_id : int) -> None:
        req_topic = f'/{cu_id}{_SUFFIX_TX_DET}'
        self.mqtt.publish(topic=req_topic, data=cu_id)


    def process_incomming_msg(self) -> None:
        self.mqtt.process_data()


#######################            FUNCTIONS             #######################
