#!/usr/bin/python3
"""
Wrapper for the MQTT client
"""
#######################        MANDATORY IMPORTS         #######################
from __future__ import annotations
#######################         GENERIC IMPORTS          #######################
from typing import List
from datetime import datetime, timedelta

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
from wattrex_cycler_datatypes.comm_data import CommDataCuC, CommDataHeartbeatC,\
    CommDataDeviceC
from wattrex_driver_db import DrvDbDetectedDeviceC, DrvDbSqlEngineC, DrvDbTypeE,\
                            DrvDbComputationalUnitC, DrvDbAvailableCuE, DrvDbConnStatusE

#######################              ENUMS               #######################

TIMEOUT_BETWEEN_CONNECTIONS=15 # 15s

#######################             CLASSES              #######################

class DbFacadeC:
    '''This function is used to create a DbFacade class for the Django backend .
    '''

    def __init__(self) -> None:
        self.database : DrvDbSqlEngineC  = DrvDbSqlEngineC(db_type=DrvDbTypeE.MASTER_DB,
                                            config_file='./devops/mn_manager/.cred.yaml')
        self.last_cu_id = -1


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


    def is_cu_registered(self, cu_info : CommDataCuC) -> bool:
        '''Check if a CU is already registered.

        Args:
            cu_info (CommDataCuC): [description]

        Returns:
            bool: [description]
        '''
        result = False
        stmt = select(DrvDbComputationalUnitC)\
                        .where(DrvDbComputationalUnitC.MAC == cu_info.mac)
        db_result = self.database.session.execute(stmt).first()
        if db_result is not None:
            result = True
        return result


    def get_cu_by_mac(self, mac : int) -> int|None:
        '''Returns the CU_ID from database for the given mac address.
        Returns None if not found.

        Args:
            mac (int): [description]

        Returns:
            result (int|None): CU_ID retrieved from database. None if not found
        '''
        result : int = None
        stmt = select(DrvDbComputationalUnitC)\
                        .where(DrvDbComputationalUnitC.MAC == mac)
        db_result = self.database.session.execute(stmt).first()
        if db_result is not None:
            query_result : DrvDbComputationalUnitC = db_result[0]
            result = query_result.CUID
        return result


    def register_cu(self, cu_info : CommDataCuC) -> None:
        '''Register a CU data unit.

        Args:
            cu_info (CommDataCuC): [description]
        '''
        log.info(f"Registering new CU: {cu_info}")
        self.last_cu_id += 1
        cu_db = DrvDbComputationalUnitC()
        cu_db.CUID = self.last_cu_id
        cu_db.MAC = cu_info.mac
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
                        .values(LastConnection= datetime.utcnow())
        self.database.session.execute(stmt)


    def update_devices(self, cu_id : int, devices : List[CommDataDeviceC]) -> None:
        '''Add or Update the list of devices in the database.

        Args:
            cu_id (int): [description]
            devices (List[CommDataDeviceC]): [description]
        '''
        select_stmt = select(DrvDbDetectedDeviceC)\
                            .where(DrvDbDetectedDeviceC.CUID == cu_id)
        res = self.database.session.execute(select_stmt).fetchall()
        for db_dev in res:
            db_dev : DrvDbDetectedDeviceC = db_dev[0]
            db_dev.ConnStatus = DrvDbConnStatusE.DISCONNECTED.value
            log.debug(f"Set device: {db_dev.__dict__} as disconnected")
            update_stmt = update(DrvDbDetectedDeviceC)\
                            .where(DrvDbDetectedDeviceC.CUID == db_dev.CUID)\
                            .where(DrvDbDetectedDeviceC.CompDevID == db_dev.CompDevID)\
                            .where(DrvDbDetectedDeviceC.SN == db_dev.SN)\
                            .where(DrvDbDetectedDeviceC.LinkName == db_dev.LinkName)\
                            .values(ConnStatus=DrvDbConnStatusE.DISCONNECTED.value)
            self.database.session.execute(update_stmt)
        msg = f"Setting as disconnected all devices in: {cu_id} to update only the connected ones"
        log.info(msg)
        self.commit()
        for device in devices:
            select_stmt = select(DrvDbDetectedDeviceC)\
                            .where(DrvDbDetectedDeviceC.CUID == cu_id)\
                            .where(DrvDbDetectedDeviceC.CompDevID == device.comp_dev_id)\
                            .where(DrvDbDetectedDeviceC.SN == device.serial_number)\
                            .where(DrvDbDetectedDeviceC.LinkName == device.link_name)
            res = self.database.session.execute(select_stmt).first()
            if res is not None:
                db_dev : DrvDbDetectedDeviceC = res[0]
                db_dev.ConnStatus = DrvDbConnStatusE.CONNECTED.value
                log.info(f"Updating device: {device}")
                update_stmt = update(DrvDbDetectedDeviceC)\
                            .where(DrvDbDetectedDeviceC.CUID == cu_id)\
                            .where(DrvDbDetectedDeviceC.CompDevID == device.comp_dev_id)\
                            .where(DrvDbDetectedDeviceC.SN == device.serial_number)\
                            .where(DrvDbDetectedDeviceC.LinkName == device.link_name)\
                            .values(ConnStatus=DrvDbConnStatusE.CONNECTED.value)
                self.database.session.execute(update_stmt)
            else:
                db_dev : DrvDbDetectedDeviceC = DrvDbDetectedDeviceC()
                db_dev.CUID = cu_id
                db_dev.CompDevID = device.comp_dev_id
                db_dev.SN = device.serial_number
                db_dev.LinkName = device.link_name
                db_dev.ConnStatus = DrvDbConnStatusE.CONNECTED.value
                log.info(f"Adding device: {device}")
                self.database.session.add(db_dev)
        log.info(f"Commiting add and/or update all devices in: {cu_id}")
        self.commit()


    def track_avail_cu(self) -> None:
        '''
        Track available CUs.
        '''
        # Update DrvDbComputationalUnitC.Available if elapsed time from LastConnection
        # is less than the defined constant
        last_ts_allowed = datetime.utcnow() - timedelta(seconds=TIMEOUT_BETWEEN_CONNECTIONS)

        stmt_put_off = update(DrvDbComputationalUnitC)\
            .where(DrvDbComputationalUnitC.Available==DrvDbAvailableCuE.ON.value,\
                DrvDbComputationalUnitC.LastConnection < last_ts_allowed)\
            .values(Available=DrvDbAvailableCuE.OFF.value)

        stmt_put_on = update(DrvDbComputationalUnitC)\
            .where(DrvDbComputationalUnitC.Available==DrvDbAvailableCuE.OFF.value,\
                DrvDbComputationalUnitC.LastConnection > last_ts_allowed)\
            .values(Available=DrvDbAvailableCuE.ON.value)

        self.database.session.execute(stmt_put_off)
        self.database.session.execute(stmt_put_on)

    def commit(self) -> None:
        '''
        Commit changes to the database.

        Raise:
            Exception: if there is an error during the commit.
        '''
        self.database.commit_changes(raise_exception=True)

#######################            FUNCTIONS             #######################
