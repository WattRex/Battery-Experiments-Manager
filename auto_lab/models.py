# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

from auto_lab.models_types import Technology_e, Chemistry_Lithium_e, Chemistry_LeadAcid_e, BipolarType_e, \
                         MembraneType_e, ElectrolyteType_e, DeviceType_e, Available_e, ExperimentStatus_e, \
                         DeviceStatus_e, Mode_e, LimitType_e, Polarity_e, ConnStatus_e, PowerMode_e


class Battery(models.Model):
    bat_id = models.AutoField(db_column='BatID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=30)  # Field name made lowercase.
    description = models.CharField(db_column='Description', max_length=250, blank=True, null=True)  # Field name made lowercase.
    manufacturer = models.CharField(db_column='Manufacturer', max_length=20)  # Field name made lowercase.
    model = models.CharField(db_column='Model', max_length=20)  # Field name made lowercase.
    sn = models.CharField(db_column='SN', max_length=30)  # Field name made lowercase.
    fab_date = models.DateField(db_column='FabDate')  # Field name made lowercase.
    tech = models.CharField(db_column='Tech', max_length=15, choices=Technology_e.choices)  # Field name made lowercase.
    cells_num = models.PositiveIntegerField(db_column='CellsNum')  # Field name made lowercase.
    cell_volt_min = models.PositiveIntegerField(db_column='CellVoltMin', blank=True, null=True)  # Field name made lowercase.
    cell_volt_max = models.PositiveIntegerField(db_column='CellVoltMax', blank=True, null=True)  # Field name made lowercase.
    volt_min = models.PositiveIntegerField(db_column='VoltMin')  # Field name made lowercase.
    volt_max = models.PositiveIntegerField(db_column='VoltMax')  # Field name made lowercase.
    curr_min = models.IntegerField(db_column='CurrMin')  # Field name made lowercase.
    curr_max = models.IntegerField(db_column='CurrMax')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Battery'
        unique_together = (('name', 'manufacturer', 'model', 'sn'),)


class Lithium(models.Model):
    bat_id = models.OneToOneField(Battery, models.DO_NOTHING, db_column='BatID', primary_key=True)  # Field name made lowercase.
    capacity = models.PositiveIntegerField(db_column='Capacity')  # Field name made lowercase.
    chemistry = models.CharField(db_column='Chemistry', max_length=5, choices=Chemistry_Lithium_e.choices)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Lithium'


class Leadacid(models.Model):
    bat_id = models.OneToOneField(Battery, models.DO_NOTHING, db_column='BatID', primary_key=True)  # Field name made lowercase.
    capacity = models.PositiveIntegerField(db_column='Capacity')  # Field name made lowercase.
    chemistry = models.CharField(db_column='Chemistry', max_length=6, choices=Chemistry_LeadAcid_e.choices)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'LeadAcid'


class Redoxstack(models.Model):
    bat_id = models.OneToOneField(Battery, models.DO_NOTHING, db_column='BatID', primary_key=True)  # Field name made lowercase.
    electrode_size = models.PositiveIntegerField(db_column='ElectrodeSize')  # Field name made lowercase.
    electrode_composition = models.CharField(db_column='ElectrodeComposition', max_length=30)  # Field name made lowercase.
    bipolar_type = models.CharField(db_column='BipolarType', max_length=20, choices=BipolarType_e.choices)  # Field name made lowercase.
    membrane_type = models.CharField(db_column='MembraneType', max_length=20, choices=MembraneType_e.choices)  # Field name made lowercase.
    electrolyte_type = models.CharField(db_column='ElectrolyteType', max_length=20, choices=ElectrolyteType_e.choices)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'RedoxStack'


class Compatibledevices(models.Model):
    comp_dev_id = models.AutoField(db_column='CompDevID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=30)  # Field name made lowercase.
    manufacturer = models.CharField(db_column='Manufacturer', max_length=30)  # Field name made lowercase.
    model = models.CharField(db_column='Model', max_length=30)  # Field name made lowercase.
    device_type = models.CharField(db_column='DeviceType', max_length=10, choices=DeviceType_e.choices)  # Field name made lowercase.
    min_sw_version = models.PositiveSmallIntegerField(db_column='MinSWVersion')  # Field name made lowercase.
    volt_min = models.PositiveIntegerField(db_column='VoltMin', blank=True, null=True)  # Field name made lowercase.
    volt_max = models.PositiveIntegerField(db_column='VoltMax', blank=True, null=True)  # Field name made lowercase.
    curr_min = models.IntegerField(db_column='CurrMin', blank=True, null=True)  # Field name made lowercase.
    curr_max = models.IntegerField(db_column='CurrMax', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CompatibleDevices'
        unique_together = (('name', 'manufacturer', 'device_type'),)


class Linkconfiguration(models.Model):
    comp_dev_id = models.ForeignKey(Compatibledevices, models.DO_NOTHING, db_column='CompDevID')  # Field name made lowercase.
    property = models.CharField(db_column='Property', max_length=30)  # Field name made lowercase.
    value = models.CharField(db_column='Value', max_length=30)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'LinkConfiguration'
        unique_together = (('comp_dev_id', 'property'),)


class Computationalunit(models.Model):
    cu_id = models.AutoField(db_column='CUID', primary_key=True)  # Field name made lowercase.
    host_name = models.CharField(db_column='HostName', max_length=50)  # Field name made lowercase.
    ip = models.CharField(db_column='IP', max_length=20)  # Field name made lowercase.
    port = models.PositiveSmallIntegerField(db_column='Port')  # Field name made lowercase.
    user = models.CharField(db_column='User', max_length=20)  # Field name made lowercase.
    last_connection = models.DateTimeField(db_column='LastConnection')  # Field name made lowercase.
    available = models.CharField(db_column='Available', max_length=3, choices=Available_e.choices)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ComputationalUnit'
        unique_together = (('host_name', 'ip', 'port'),)


class Cyclerstation(models.Model):
    cs_id = models.AutoField(db_column='CSID', primary_key=True)  # Field name made lowercase.
    cu_id = models.ForeignKey(Computationalunit, models.DO_NOTHING, db_column='CUID')  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=30)  # Field name made lowercase.
    location = models.CharField(db_column='Location', max_length=30)  # Field name made lowercase.
    register_date = models.DateTimeField(db_column='RegisterDate')  # Field name made lowercase.
    parent = models.PositiveIntegerField(db_column='Parent', blank=True, null=True)  # Field name made lowercase.
    deprecated = models.IntegerField(db_column='Deprecated')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CyclerStation'


class Detecteddevices(models.Model):
    dev_id = models.AutoField(db_column='DevID', primary_key=True)  # Field name made lowercase.
    cu_id = models.ForeignKey(Computationalunit, models.DO_NOTHING, db_column='CUID')  # Field name made lowercase.
    comp_dev_id = models.ForeignKey(Compatibledevices, models.DO_NOTHING, db_column='CompDevID')  # Field name made lowercase.
    sn = models.CharField(db_column='SN', max_length=30)  # Field name made lowercase.
    link_name = models.CharField(db_column='LinkName', max_length=30)  # Field name made lowercase.
    conn_status = models.CharField(db_column='ConnStatus', max_length=12)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DetectedDevices'
        unique_together = (('cu_id', 'comp_dev_id', 'link_name'),)


class Useddevices(models.Model):
    csid = models.ForeignKey(Cyclerstation, models.DO_NOTHING, db_column='CSID')  # Field name made lowercase.
    devid = models.ForeignKey(Detecteddevices, models.DO_NOTHING, db_column='DevID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'UsedDevices'
        unique_together = (('csid', 'devid'),)


class Availablemeasures(models.Model):
    meas_type = models.AutoField(db_column='MeasType', primary_key=True)  # Field name made lowercase.
    comp_dev_id = models.ForeignKey('Compatibledevices', models.DO_NOTHING, db_column='CompDevID')  # Field name made lowercase.
    meas_name = models.CharField(db_column='MeasName', max_length=20)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AvailableMeasures'


class Usedmeasures(models.Model):
    used_meas_id = models.AutoField(db_column='UsedMeasID', primary_key=True)  # Field name made lowercase.
    cs_id = models.ForeignKey(Cyclerstation, models.DO_NOTHING, db_column='CSID')  # Field name made lowercase.
    dev_id = models.ForeignKey(Useddevices, models.DO_NOTHING, db_column='DevID')  # Field name made lowercase.
    meas_type = models.ForeignKey(Availablemeasures, models.DO_NOTHING, db_column='MeasType')  # Field name made lowercase.
    custom_name = models.CharField(db_column='CustomName', max_length=30, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'UsedMeasures'


class Profile(models.Model):
    prof_id = models.AutoField(db_column='ProfID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=40)  # Field name made lowercase.
    description = models.CharField(db_column='Description', max_length=250)  # Field name made lowercase.
    volt_max = models.PositiveIntegerField(db_column='VoltMax', blank=True, null=True)  # Field name made lowercase.
    volt_min = models.PositiveIntegerField(db_column='VoltMin', blank=True, null=True)  # Field name made lowercase.
    curr_max = models.IntegerField(db_column='CurrMax', blank=True, null=True)  # Field name made lowercase.
    curr_min = models.IntegerField(db_column='CurrMin', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Profile'


class Experiment(models.Model):
    exp_id = models.AutoField(db_column='ExpID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=30)  # Field name made lowercase.
    description = models.CharField(db_column='Description', max_length=250)  # Field name made lowercase.
    date_creation = models.DateTimeField(db_column='DateCreation')  # Field name made lowercase.
    date_begin = models.DateTimeField(db_column='DateBegin', blank=True, null=True)  # Field name made lowercase.
    date_finish = models.DateTimeField(db_column='DateFinish', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='Status', max_length=8, choices=ExperimentStatus_e.choices)  # Field name made lowercase.
    cs_id = models.ForeignKey(Cyclerstation, models.DO_NOTHING, db_column='CSID')  # Field name made lowercase.
    bat_id = models.ForeignKey(Battery, models.DO_NOTHING, db_column='BatID')  # Field name made lowercase.
    prof_id = models.ForeignKey(Profile, models.DO_NOTHING, db_column='ProfID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Experiment'


class Alarm(models.Model):
    exp_id = models.ForeignKey(Experiment, models.DO_NOTHING, db_column='ExpID')  # Field name made lowercase.
    alarm_id = models.PositiveIntegerField(db_column='AlarmID', primary_key=True)  # Field name made lowercase.
    timestamp = models.DateTimeField(db_column='Timestamp')  # Field name made lowercase.
    code = models.PositiveIntegerField(db_column='Code')  # Field name made lowercase.
    value = models.IntegerField(db_column='Value')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Alarm'
        unique_together = (('exp_id', 'alarm_id'),)


class Devicestatus(models.Model):
    status_id = models.PositiveIntegerField(db_column='StatusID')  # Field name made lowercase.
    exp_id = models.ForeignKey(Experiment, models.DO_NOTHING, db_column='ExpID')  # Field name made lowercase.
    dev_id = models.ForeignKey(Detecteddevices, models.DO_NOTHING, db_column='DevID')  # Field name made lowercase.
    timestamp = models.DateTimeField(db_column='Timestamp')  # Field name made lowercase.
    status = models.CharField(db_column='Status', max_length=20, choices=DeviceStatus_e.choices)  # Field name made lowercase.
    error_code = models.PositiveSmallIntegerField(db_column='ErrorCode')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Status'
        unique_together = (('status_id', 'exp_id'),)


class Redoxelectrolyte(models.Model):
    exp_id = models.ForeignKey(Experiment, models.DO_NOTHING, db_column='ExpID')  # Field name made lowercase.
    bat_id = models.ForeignKey(Redoxstack, models.DO_NOTHING, db_column='BatID')  # Field name made lowercase.
    polarity = models.CharField(db_column='Polarity', max_length=3, choices=Polarity_e.choices)  # Field name made lowercase.
    electrolyte_vol = models.PositiveIntegerField(db_column='ElectrolyteVol')  # Field name made lowercase.
    initial_soc = models.PositiveIntegerField(db_column='InitialSOC')  # Field name made lowercase.
    min_flow_rate = models.PositiveIntegerField(db_column='MinFlowRate')  # Field name made lowercase.
    max_flow_rate = models.PositiveIntegerField(db_column='MaxFlowRate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'RedoxElectrolyte'
        unique_together = (('exp_id', 'bat_id', 'polarity'),)


class Instructions(models.Model):
    instr_id = models.PositiveIntegerField(db_column='InstrID', primary_key=True)  # Field name made lowercase.
    prof_id = models.ForeignKey(Profile, models.DO_NOTHING, db_column='ProfID')  # Field name made lowercase.
    mode = models.CharField(db_column='Mode', max_length=7, choices=Mode_e.choices)  # Field name made lowercase.
    set_point = models.IntegerField(db_column='SetPoint')  # Field name made lowercase.
    limit_type = models.CharField(db_column='LimitType', max_length=7, choices=LimitType_e.choices)  # Field name made lowercase.
    limit_point = models.IntegerField(db_column='LimitPoint')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Instructions'
        unique_together = (('instr_id', 'prof_id'),)


class Genericmeasures(models.Model):
    exp_id = models.ForeignKey(Experiment, models.DO_NOTHING, db_column='ExpID')  # Field name made lowercase.
    meas_id = models.PositiveIntegerField(db_column='MeasID', primary_key=True)  # Field name made lowercase.
    timestamp = models.DateTimeField(db_column='Timestamp')  # Field name made lowercase.
    instr_id = models.ForeignKey(Instructions, models.DO_NOTHING, db_column='InstrID')  # Field name made lowercase.
    voltage = models.PositiveIntegerField(db_column='Voltage')  # Field name made lowercase.
    current = models.IntegerField(db_column='Current')  # Field name made lowercase.
    power = models.IntegerField(db_column='Power')  # Field name made lowercase.
    power_mode = models.CharField(db_column='PowerMode', max_length=7, choices=PowerMode_e.choices)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GenericMeasures'
        unique_together = (('exp_id', 'meas_id'),)


class Extendedmeasures(models.Model):
    exp_id = models.ForeignKey(Experiment, models.DO_NOTHING, db_column='ExpID')  # Field name made lowercase.
    meas_id = models.ForeignKey(Genericmeasures, models.DO_NOTHING, db_column='MeasID')  # Field name made lowercase.
    used_meas_id = models.ForeignKey(Usedmeasures, models.DO_NOTHING, db_column='UsedMeasID')  # Field name made lowercase.
    value = models.IntegerField(db_column='Value')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ExtendedMeasures'
        unique_together = (('exp_id', 'used_meas_id', 'meas_id'),)
