#!/usr/bin/python3
"""
Wrapper for the MQTT client
"""
#######################        MANDATORY IMPORTS         #######################

#######################         GENERIC IMPORTS          #######################
from typing import List
from datetime import datetime

#######################       THIRD PARTY IMPORTS        #######################
from sqlalchemy.sql.expression import update, select

#######################    SYSTEM ABSTRACTION IMPORTS    #######################
from system_logger_tool import sys_log_logger_get_module_logger, SysLogLoggerC, Logger

#######################       LOGGER CONFIGURATION       #######################
if __name__ == '__main__':
    cycler_logger = SysLogLoggerC(file_log_levels='../log_config.yaml')
log: Logger = sys_log_logger_get_module_logger(__name__)

#######################          MODULE IMPORTS          #######################

#######################          PROJECT IMPORTS         #######################
from wattrex_battery_cycler_datatypes.comm_data import CommDataCuC, CommDataHeartbeatC,\
    CommDataDeviceC
from wattrex_driver_db import DrvDbDetectedDeviceC, DrvDbSqlEngineC, DrvDbTypeE,\
                            DrvDbComputationalUnitC, DrvDbAvailableCuE, DrvDbConnStatusE

#######################              ENUMS               #######################

#######################             CLASSES              #######################

class DbFacadeC:
    '''This function is used to create a DbFacade class for the Django backend .
    '''

    def __init__(self) -> None:
        self.database : DrvDbSqlEngineC  = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                                            config_file='.cred.yaml')
        self.last_cu_id = 0


    def get_last_cu_id(self) -> int:
        '''Get the CUDA CU ID for this simulation.

        Returns:
            int: [description]
        '''
        stmt = select(DrvDbComputationalUnitC.CUID)\
                        .order_by(DrvDbComputationalUnitC.CUID.desc())\
                        .limit(1)
        res = self.database.session.execute(stmt).first()
        if res is not None:
            self.last_cu_id = res[0]

        return self.last_cu_id

    def get_available_cus(self) -> List[int]:
        '''Returns a list of available CUDA units.

        Returns:
            List[int]: [description]
        '''
        stmt = select(DrvDbComputationalUnitC.CUID)\
                        .filter(DrvDbComputationalUnitC.Available == DrvDbAvailableCuE.ON.value)\
                        .order_by(DrvDbComputationalUnitC.CUID.asc())
        res = self.database.session.execute(stmt).fetchall()
        cus = []
        for c_unit in res:
            cus.append(c_unit[0])
        return cus


    def register_cu(self, cu_info : CommDataCuC) -> None:
        '''Register a CU data unit.

        Args:
            cu_info (CommDataCuC): [description]
        '''
        log.info(f"Registering new CU: {cu_info}")
        self.last_cu_id += 1
        cu_db = DrvDbComputationalUnitC()
        cu_db.CUID = self.last_cu_id
        cu_db.HostName = cu_info.hostname
        cu_db.User = cu_info.user
        cu_db.IP = cu_info.ip
        cu_db.Port = cu_info.port
        cu_db.LastConnection = datetime.utcnow()
        cu_db.Available = DrvDbAvailableCuE.ON.value
        self.database.session.add(cu_db)


    def update_heartbeat(self, heartbeat : CommDataHeartbeatC) -> None:
        '''Update the commData of the commdata.

        Args:
            hb (CommDataHeartbeatC): [description]
        '''
        stmt = update(DrvDbComputationalUnitC)\
                        .where(DrvDbComputationalUnitC.CUID == heartbeat.cu_id)\
                        .values(LastConnection= heartbeat.timestamp)
        self.database.session.execute(stmt)


    def update_devices(self, cu_id : int, devices : List[CommDataDeviceC]) -> None:
        '''Update the list of devices in the database.

        Args:
            cu_id (int): [description]
            devices (List[CommDataDeviceC]): [description]
        '''
        for device in devices:
            db_dev = DrvDbDetectedDeviceC()
            db_dev.CUID = cu_id
            db_dev.CompDevID = device.comp_dev_id
            db_dev.SN = device.serial_number
            db_dev.LinkName = device.link_name
            db_dev.ConnStatus = DrvDbConnStatusE.CONNECTED.value
            self.database.session.add(db_dev)
            log.info(f"Adding device: {device.__dict__}")
            # TODO: add str for CommDataDeviceC
            # TODO: use add or update: depending if exists or not

    def track_avail_cu(self) -> None:
        '''Track available CUs.
        '''
        # TODO: implement this function


    def commit(self) -> None:
        '''
        Commit changes to the database.

        Raise:
            Exception: if there is an error during the commit.
        '''
        self.database.commit_changes(raise_exception=True)

#######################            FUNCTIONS             #######################