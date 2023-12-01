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
    Model           varchar(30)                 not null,
    DeviceType      enum ('Source', 'BiSource', 'Load', 'Meter', 'Epc', 'Bms', 'Bk', 'Flow') not null,      -- Source, BiSource, Load, Meter, Epc
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


-- Table LinkConfiguration --------------------------
create table if not exists LinkConfiguration
(
    CompDevID       mediumint       unsigned    not null,
    Property        varchar(30)                 not null,
    Value           varchar(30)                 not null,

    constraint LinkConfiguration_pk_1
        primary key (CompDevID, Property),
    constraint LinkConfiguration_fk_1
        foreign key (CompDevID) references CompatibleDevices (CompDevID)
);


-- Table ComputationalUnit --------------------------
create table if not exists ComputationalUnit
(
    CUID            mediumint       unsigned    not null    auto_increment,
    MAC             varchar(30)                 not null,
    HostName        varchar(50)                 not null,
    IP              varchar(20)                 not null,
    Port            smallint        unsigned    not null,
    User            varchar(30)                 not null,
    LastConnection  datetime                    not null,
    Available       enum ('ON', 'OFF')          not null,

    constraint ComputationalUnit_pk_1
        primary key (CUID),
    constraint ComputationalUnit_unq_1
        unique (MAC, HostName, IP, Port)
);


-- Table CyclerStation --------------------------
create table if not exists CyclerStation
(
    CSID            mediumint       unsigned    not null    auto_increment,
    CUID            mediumint       unsigned    not null,
    Name            varchar(30)                 not null,
    Location        varchar(30)                 not null,
    RegisterDate    datetime                    not null,
    Parent          mediumint       unsigned        null,
    Deprecated      boolean                     not null,
    
    constraint CycleStation_pk_1
        primary key (CSID),
    constraint CycleStation_fk_1
        foreign key (CUID) references ComputationalUnit (CUID)
);


-- Table DetectedDevices --------------------------
create table if not exists DetectedDevices
(
    DevID           mediumint       unsigned    not null    auto_increment,
    CUID            mediumint       unsigned    not null,
    CompDevID       mediumint       unsigned    not null,
    SN              varchar(30)                 not null,                       -- Laboratory Invetory label
    LinkName        varchar(30)                 not null,                       -- Name of the device in the computational unit (udev or can id)
    ConnStatus      enum ('CONNECTED', 'DISCONNECTED') not null,

    constraint DetectedDevices_pk_1
        primary key (DevID),
    constraint DetectedDevices_fk_1
        foreign key (CompDevID) references CompatibleDevices (CompDevID),
    constraint DetectedDevices_fk_2
        foreign key (CUID) references ComputationalUnit (CUID),
    constraint DetectedDevices_unq_1
        unique (CUID, CompDevID, LinkName)
);


-- Table UsedDevices --------------------------
create table if not exists UsedDevices
(
    CSID            mediumint       unsigned    not null,
    DevID           mediumint       unsigned    not null,

    constraint UsedDevices_pk_1
        primary key (CSID, DevID),
    constraint UsedDevices_fk_1
        foreign key (CSID) references CyclerStation (CSID),
    constraint UsedDevices_fk_2
        foreign key (DevID) references DetectedDevices (DevID)
);


-- Table AvailableMeasures --------------------------
create table if not exists AvailableMeasures
(
    MeasType        mediumint       unsigned    not null    auto_increment,
    CompDevID       mediumint       unsigned    not null,
    MeasName        varchar(20)                 not null,

    constraint AvailableMeasures_pk_1
        primary key (MeasType),
    constraint AvailableMeasures_fk_1
        foreign key (CompDevID) references CompatibleDevices (CompDevID)
);


-- Table UsedMeasures --------------------------
create table if not exists UsedMeasures
(
    UsedMeasID      mediumint       unsigned    not null    auto_increment,
    CSID            mediumint       unsigned    not null,
    DevID           mediumint       unsigned    not null,
    MeasType        mediumint       unsigned    not null,
    CustomName      varchar(30)                 null,

    constraint UsedMeasures_pk_1
        primary key (UsedMeasID),
    constraint UsedMeasures_fk_1
        foreign key (CSID) references CyclerStation (CSID),
    constraint UsedMeasures_fk_2
        foreign key (DevID)  references UsedDevices (DevID),
    constraint UsedMeasures_fk_3
        foreign key (MeasType) references AvailableMeasures (MeasType)
);


-- Table Profile -------------------------------
create table if not exists Profile
(
    ProfID          mediumint       unsigned    not null    auto_increment,
    Name            varchar(40)                 not null,
    Description     varchar(250)                not null,
    VoltMax         mediumint       unsigned        null,
    VoltMin         mediumint       unsigned        null,
    CurrMax         mediumint                       null,
    CurrMin         mediumint                       null,

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
    DateBegin       datetime                        null,
    DateFinish      datetime                        null,
    Status          enum ('RUNNING', 'FINISHED', 'ERROR', 'PAUSED', 'QUEUED') not null,       -- RUNNING, FINISHED, ERROR, PAUSED, QUEUED
    CSID            mediumint       unsigned    not null,
    BatID           mediumint       unsigned    not null,
    ProfID          mediumint       unsigned    not null,

    constraint Experiment_pk_1
        primary key (ExpID),
    constraint Experiment_fk_1
        foreign key (CSID) references CyclerStation (CSID),
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
    StatusID        mediumint       unsigned    not null,                       -- reset to 1 for each experiment
    ExpID           mediumint       unsigned    not null,
    DevID           mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    Status          enum ('OK', 'COMM_ERROR', 'INTERNAL_ERROR') not null,
    ErrorCode       smallint        unsigned    not null,
    
    constraint Status_pk_1
        primary key (StatusID, ExpID),
    constraint Status_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint Status_fk_2
        foreign key (DevID) references DetectedDevices (DevID)
);


-- Table RedoxElectrolyte --------------------------
create table if not exists RedoxElectrolyte
(
    ExpID           mediumint       unsigned    not null,
    BatID           mediumint       unsigned    not null,
    Polarity        enum ('POS', 'NEG')         not null,
    ElectrolyteVol  mediumint       unsigned    not null,
    InitialSOC      mediumint       unsigned    not null,
    MinFlowRate     mediumint       unsigned    not null,
    MaxFlowRate     mediumint       unsigned    not null,

    constraint RedoxElectrolyte_pk_1 
        primary key (ExpID, BatID, Polarity),
    constraint RedoxElectrolyte_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint RedoxElectrolyte_fk_2
        foreign key (BatID) references RedoxStack (BatID)
);


-- Table Instructions --------------------------
create table if not exists Instructions
(
    InstrID         mediumint       unsigned    not null,
    ProfID          mediumint       unsigned    not null,
    Mode            enum ('WAIT', 'CC_MODE', 'CV_MODE', 'CP_MODE') not null,    -- WAIT, CC, CV, CP
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
    MeasID          int             unsigned    not null,
    ExpID           mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    InstrID         mediumint       unsigned    not null,
    Voltage         mediumint       unsigned    not null,
    Current         mediumint                   not null,
    Power           int                   not null,
    PowerMode       enum ('DISABLE', 'WAIT', 'CC_MODE', 'CV_MODE', 'CP_MODE') not null,

    constraint GenericMeasures_pk_1
        primary key (MeasID, ExpID),
    constraint GenericMeasures_fk_1
        foreign key (ExpID) references Experiment (ExpID),
    constraint GenericMeasures_fk_2
        foreign key (InstrID) references Instructions (InstrID)
);


-- Table ExtendedMeasures --------------------------
create table if not exists ExtendedMeasures
(
    ExpID           mediumint       unsigned    not null,
    MeasID          int             unsigned    not null,
    UsedMeasID      mediumint       unsigned    not null,
    Value           mediumint                   not null,

    constraint ExtendedMeasures_pk_1 
        primary key (ExpID, MeasID, UsedMeasID),
    constraint ExtendedMeasures_fk_1
        foreign key (ExpID, MeasID) references GenericMeasures (ExpID, MeasID),
    constraint ExtendedMeasures_fk_2
        foreign key (UsedMeasID) references UsedMeasures (UsedMeasID)
);

INSERT INTO CompatibleDevices(Name, Manufacturer, Model, DeviceType, MinSWVersion, VoltMin, VoltMax, CurrMin, CurrMax) VALUES ('Virtual', 'Undefined', 'Undefined', 'BiSource', 0, 0, 9999999, -999999, 999999);
INSERT INTO ComputationalUnit(MAC, HostName, IP, Port, User, LastConnection, Available) VALUES ('0x000000000000', 'Virtual', '127.0.0.1', 6969, 'basic_user', NOW(), 'ON');
INSERT INTO CyclerStation(CUID, Name, Location, RegisterDate, Deprecated) VALUES (1, 'Virtual', 'Undefined', NOW(), 0);
INSERT INTO DetectedDevices(CUID, CompDevID, SN, LinkName, ConnStatus) VALUES (1, 1, 'Virtual', 'Virtual', 'CONNECTED');
INSERT INTO UsedDevices(CSID, DevID) VALUES (1, 1);
