-- Table Battery --------------------------
create table if not exists Battery
(
    BatID           mediumint       unsigned    not null    auto_increment,
    Name            varchar(30)                 not null,
    Description     varchar(250)                null,
    Manufacturer    varchar(20)                 not null,
    Model           varchar(20)                 not null,
    SN              varchar(30)                 not null,
    FabDate         date                        not null,
    Tech            enum ('Lithium', 'LeadAcid', 'RedoxStack') not null,
    CellsNum        mediumint                   not null,
    CellVoltMin     mediumint       unsigned    null,
    CellVoltMax     mediumint       unsigned    null,
    VoltMin         mediumint       unsigned    not null,
    VoltMax         mediumint       unsigned    not null,
    CurrMin         mediumint                   not null,
    CurrMax         mediumint                   not null,

    constraint Battery_pk_1
        primary key (BatID),
    constraint Battery_unq_1
        unique (Name, Manufacturer, Model, SN)
);


-- Table Lithium --------------------------
create table if not exists Lithium
(
    BatID           mediumint       unsigned    not null,
    Capacity        mediumint       unsigned    not null,
    Chemistry       enum ('NMC', 'NCA', 'LMO', 'LFP', 'LCO', 'Other') not null,

    constraint Lithium_pk_1
        primary key (BatID),
    constraint Lithium_fk_1
        foreign key (BatID) references Battery (BatID)
);


-- Table LeadAcid --------------------------
create table if not exists LeadAcid
(
    BatID           mediumint       unsigned    not null,
    Capacity        mediumint       unsigned    not null,
    Chemistry       enum ('Liquid', 'Gel', 'Other') not null,

    constraint LeadAcid_pk_1
        primary key (BatID),
    constraint LeadAcid_fk_1
        foreign key (BatID) references Battery (BatID)
);


-- Table RedoxStack --------------------------
create table if not exists RedoxStack
(
    BatID           mediumint       unsigned    not null,
    ElectrodeSize   mediumint       unsigned    not null,
    ElectrodeComposition varchar(30)            not null,
    BipolarType     enum ('Papyex Mersen', 'Composite Schunk', 'Graphite', 'Other') not null,
    MembraneType    enum ('Fumasep-Anionic', 'Fumasep-Cathionic', 'Nafion', 'Vanadion', 'PEEK', 'Other') not null,
    ElectrolyteType enum ('All-vanadium', 'All-iron', 'Vanadium-based', 'Iron-based', 'Other') not null,

    constraint RedoxStack_pk_1
        primary key (BatID),
    constraint RedoxStack_fk_1
        foreign key (BatID) references Battery (BatID)
);


-- Table CompatibleDevices --------------------------
create table if not exists CompatibleDevices
(
    CompDevID       mediumint       unsigned    not null    auto_increment,
    Name            varchar(30)                 not null,
    Manufacturer    varchar(30)                 not null,
    DeviceType      enum ('Source', 'BiSource', 'Load', 'Meter') not null,      -- Source, BiSource, Load, Meter
    MinSWVersion    smallint        unsigned    not null,
    VoltMin         mediumint       unsigned    null,
    VoltMax         mediumint       unsigned    null,
    CurrMin         mediumint                   null,
    CurrMax         mediumint                   null,

    constraint CompatibleDevices_pk_1
        primary key (CompDevID),
    constraint CompatibleDevices_unq_1
        unique (Name, Manufacturer, DeviceType)
);


-- Table ComputationalUnit --------------------------
create table if not exists ComputationalUnit
(
    CUID            mediumint       unsigned    not null    auto_increment,
    Name            varchar(50)                 not null,
    IP              varchar(20)                 not null,
    Port            smallint        unsigned    not null,
    User            varchar(20)                 not null,
    Pass            varchar(100)                not null,
    LastConnection   datetime                    not null,
    Available       enum ('ON', 'OFF')          not null,

    constraint ComputationalUnit_pk_1
        primary key (CUID),
    constraint ComputationalUnit_unq_1
        unique (Name, IP, Port)
);


-- Table CycleStation --------------------------
create table if not exists CycleStation
(
    CSID            mediumint       unsigned    not null    auto_increment,
    CUID            mediumint       unsigned    not null,
    Name            varchar(30)                 not null,
    Location        varchar(30)                 not null,
    RegisterDate    datetime                    not null,
    
    constraint CycleStation_pk_1
        primary key (CSID, CUID),
    constraint CycleStation_fk_1
        foreign key (CUID) references ComputationalUnit (CUID)
);


-- Table UsedDevices --------------------------
create table if not exists UsedDevices
(
    DevID           mediumint       unsigned    not null,
    CSID            mediumint       unsigned    not null,
    CompDevID       mediumint       unsigned    not null,
    SN              varchar(30)                 not null,                        -- Laboratory Invetory label
    UdevName        varchar(30)                 not null,

    constraint UsedDevices_pk_1
        primary key (DevID, CSID),
    constraint UsedDevices_fk_1
        foreign key (CSID) references CycleStation (CSID),
    constraint UsedDevices_fk_2
        foreign key (CompDevID) references CompatibleDevices (CompDevID),
    constraint UsedDevices_unq_1
        unique (CSID, CompDevID, SN)
);


-- Table Profile --------------------------
create table if not exists Profile
(
    ProfID           mediumint       unsigned    not null    auto_increment,
    Name            varchar(40)                 not null,
    Description     varchar(250)                not null,
    VoltMax         mediumint       unsigned        null,
    VoltMin         mediumint       unsigned        null,
    CurrMax         mediumint                   not null,
    CurrMin         mediumint                   not null,

    constraint profile_pf_1
        primary key (ProfID)
);


-- Table Experiment --------------------------
create table if not exists Experiment
(
    ExpID           mediumint       unsigned    not null    auto_increment,
    Name            varchar(30)                 not null,
    Description     varchar(250)                not null,
    DateCreation    datetime                    not null,
    DateBegin       datetime                    not null,
    DateFinish      datetime                    not null,
    Status          enum ('RUNNING', 'FINISHED', 'ERROR', 'PAUSED', 'QUEUED') not null,       -- RUNNING, FINISHED, ERROR, PAUSED, QUEUED
    CSID            mediumint       unsigned    not null,
    BatID           mediumint       unsigned    not null,
    ProfID          mediumint       unsigned    not null,

    constraint Experiment_pk_1
        primary key (ExpID),
    constraint Experiment_fk_1
        foreign key (CSID) references CycleStation (CSID),
    constraint Experiment_fk_2
        foreign key (BatID) references Battery (BatID),
    constraint Experiment_fk_3
        foreign key (ProfID) references Profile (ProfID)
);


-- Table Alarm --------------------------
create table if not exists Alarm
(
    ExpID           mediumint       unsigned    not null,
    AlarmID         mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    Code            mediumint       unsigned    not null,
    Value           mediumint                   not null,

    constraint Alarm_pk_1
        primary key (ExpID, AlarmID),
    constraint Alarm_fk_1
        foreign key (ExpID) references Experiment (ExpID)
);


-- Table Status --------------------------
create table if not exists Status
(
    ExpID           mediumint       unsigned    not null,
    DevID           mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    Status          enum ('OK', 'COMM_ERROR', 'INTERNAL_ERROR') not null,
    ErrorCode       smallint        unsigned    not null,
    
    constraint Status_pk_1
        primary key (ExpID, DevID),
    constraint Status_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint Status_fk_2
        foreign key (DevID) references UsedDevices (DevID)
);


-- Table RedoxElectrolyte --------------------------
create table if not exists RedoxElectrolyte
(
    ExpID           mediumint       unsigned    not null,
    BatID           mediumint       unsigned    not null,
    ElectrolyteVol  mediumint       unsigned    not null,
    MaxFlowRate     mediumint       unsigned    not null,

    constraint RedoxElectrolyte_pk_1 
        primary key (ExpID, BatID),
    constraint RedoxElectrolyte_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint RedoxElectrolyte_fk_2
        foreign key (BatID) references Battery (BatID)
);


-- Table Instructions --------------------------
create table if not exists Instructions
(
    InstrID         mediumint       unsigned    not null,
    ProfID          mediumint       unsigned    not null,
    Mode            enum ('WAIT', 'CC', 'CV', 'CP') not null,                   -- WAIT, CC, CV, CP
    SetPoint        mediumint                   not null,
    LimitType       enum ('TIME', 'VOLTAGE', 'CURRENT', 'POWER') not null,      -- TIME, VOLTAGE, CURRENT, POWER
    LimitPoint      mediumint                   not null,

    constraint Instructions_pk_1
        primary key (InstrID, ProfID),
    constraint Instructions_fk_1
        foreign key (ProfID) references Profile (ProfID)
);


-- Table GenericMeasures --------------------------
create table if not exists GenericMeasures
(
    ExpID           mediumint       unsigned    not null,
    MeasID          int             unsigned    not null,
    Timestamp       datetime                    not null,
    InstrID         mediumint       unsigned    not null,
    Voltage         mediumint                   not null,
    Current         mediumint                   not null,

    constraint GenericMeasures_pk_1
        primary key (ExpID, MeasID),
    constraint GenericMeasures_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint GenericMeasures_fk_2
        foreign key (InstrID) references Instructions (InstrID)
);


-- Table MeasuresDeclaration --------------------------
create table if not exists MeasuresDeclaration
(
    MeasType        mediumint       unsigned    not null    auto_increment,
    MeasName        varchar(20)                 not null,

    constraint MeasuresDeclaration_pk_1
        primary key (MeasType),
    constraint MeasuresDeclaration_unq_1
        unique (MeasName)
);


-- Table ExtendedMeasures --------------------------
create table if not exists ExtendedMeasures
(
    ExpID           mediumint       unsigned    not null,
    MeasType        mediumint       unsigned    not null,
    MeasID          int             unsigned    not null,
    Value           mediumint                   not null,

    constraint ExtendedMeasures_pk_1 
        primary key (ExpID, MeasType, MeasID),
    constraint ExtendedMeasures_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint ExtendedMeasures_fk_2
        foreign key (MeasType) references MeasuresDeclaration (MeasType),
    constraint ExtendedMeasures_fk_3
        foreign key (ExpID, MeasID) references GenericMeasures (ExpID, MeasID)
);

INSERT INTO CompatibleDevices(Name, Manufacturer, DeviceType, MinSWVersion, VoltMin, VoltMax, CurrMin, CurrMax) VALUES ('Virtual', 'Undefined', 'BiSource', 0, 0, 9999999, -999999, 999999);
INSERT INTO ComputationalUnit(Name, IP, Port, User, Pass, LastConnection, Available) VALUES ('Virtual', '127.0.0.1', 6969, 'basic_user', 'basic_user', NOW(), 'ON');
INSERT INTO CycleStation(CUID, Name, Location, RegisterDate) VALUES (1, 'Virtual', 'Undefined', NOW());
INSERT INTO UsedDevices(DevID, CSID, CompDevID, SN, UdevName) VALUES (1, 1, 1, 'Virtual', 'Virtual');

CREATE User 'basic_user'@'%' IDENTIFIED BY 'basic_user';
GRANT SELECT, SHOW VIEW ON battery_experiments_manager_db.* TO 'basic_user'@'%';
ALTER USER 'basic_user'@'%' IDENTIFIED WITH mysql_native_password BY 'basic_user';
FLUSH PRIVILEGES;
