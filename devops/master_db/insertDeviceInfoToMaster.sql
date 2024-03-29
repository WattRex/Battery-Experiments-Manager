INSERT INTO `CompatibleDevices` (`CompDevID`, `Name`, `Manufacturer`, `Model`, `DeviceType`, `MinSWVersion`, `VoltMin`, `VoltMax`, `CurrMin`, `CurrMax`) VALUES
    (2, 'EPC', 'Wattrex', 'A', 'Epc', 0, 0, 6000, -15000, 15000),
    (3, 'BMS', 'Liftec', '0', 'Bms', 0, NULL, NULL, NULL, NULL);

INSERT INTO `AvailableMeasures` (`MeasType`, `CompDevID`, `MeasName`) VALUES
    (1, 2, 'hs_voltage'),
    (2, 2, 'temp_body'),
    (3, 2, 'temp_amb'),
    (4, 2, 'temp_anod'),
    (5, 3, 'temp1'),
    (6, 3, 'temp2'),
    (7, 3, 'temp3'),
    (8, 3, 'temp4'),
    (9, 3, 'vcell1'),
    (10, 3, 'vcell2'),
    (11, 3, 'vcell3'),
    (12, 3, 'vcell4'),
    (13, 3, 'vcell5'),
    (14, 3, 'vcell6'),
    (15, 3, 'vcell7'),
    (16, 3, 'vcell8'),
    (17, 3, 'vcell9'),
    (18, 3, 'vcell10'),
    (19, 3, 'vcell12'),
    (20, 3, 'vstack'),
    (21, 3, 'status'),
    (22, 3, 'pres1'),
    (23, 3, 'pres2');