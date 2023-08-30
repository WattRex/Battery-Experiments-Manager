from django.db import models



class Technology_e(models.TextChoices):
    LITHIUM = 'Lithium'
    LEADACID = 'LeadAcid'
    REDOXSTACK = 'RedoxStack'

class Chemistry_Lithium_e(models.TextChoices):
    NMC = 'NMC'
    NCA = 'NCA'
    LMO = 'LMO'
    LFP = 'LFP'
    LCO = 'LCO'
    OTHER = 'Other'

class Chemistry_LeadAcid_e(models.TextChoices):
    LIQUID = 'Liquid'
    GEL = 'Gel'
    OTHER = 'Other'

class BipolarType_e(models.TextChoices):
    PAPYEX_MERSEN = 'Papyex Mersen'
    COMPOSITE_SCHUNK = 'Composite Schunk'
    GRAPHITE = 'Graphite'
    OTHER = 'Other'

class MembraneType_e(models.TextChoices):
    FUMASEP_ANIONIC = 'Fumasep-Anionic'
    FUMASEP_CATHIONIC = 'Fumasep-Cathionic'
    NAFION = 'Nafion'
    VANADION = 'Vanadion'
    PEEK = 'PEEK'
    OTHER = 'Other'

class ElectrolyteType_e(models.TextChoices):
    ALL_VANADIUM = 'All-vanadium'
    ALL_IRON = 'All-iron'
    VANADIUM_BASED = 'Vanadium-based'
    IRON_BASED = 'Iron-based'
    OTHER = 'Other'

class DeviceType_e(models.TextChoices):
    SOURCE = 'Source'
    BISOURCE = 'BiSource'
    LOAD = 'Load'
    METER = 'Meter'

class Available_e(models.TextChoices):
    ON = 'ON'
    OFF = 'OFF'

class Status_Experiment_e(models.TextChoices):
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    ERROR = 'ERROR'
    PAUSED = 'PAUSED'
    QUEUED = 'QUEUED'

class Status_DeviceStatus_e(models.TextChoices):
    OK = 'OK'
    COMM_ERROR = 'COMM_ERROR'
    INTERNAL_ERROR = 'INTERNAL_ERROR'

class Mode_e(models.TextChoices):
    WAIT = 'WAIT'
    CC = 'CC'
    CV = 'CV'
    CP = 'CP'

class LimitType_e(models.TextChoices):
    TIME = 'TIME'
    VOLTAGE = 'VOLTAGE'
    CURRENT = 'CURRENT'
    POWER = 'POWER'

