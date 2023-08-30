from enum import Enum

class VALIDATOR_Limits_e (Enum):
    LIMIT_TIME     = 'TIME'
    LIMIT_CAPACITY = 'CAPACITY'
    LIMIT_VOLTAGE  = 'VOLTAGE'
    LIMIT_CURRENT  = 'CURRENT' 

class VALIDATOR_CylingMode_e (Enum):
    # TODO: Homogenizar con el de MID_COMM
    MODE_WAIT  = 'WAIT'
    MODE_CV    = 'CV'
    MODE_CC    = 'CC'

class VALIDATOR_Instruction_c():
    def __init__(self, mode : VALIDATOR_CylingMode_e, setPoint : int, limitType : VALIDATOR_Limits_e, limit : int):
        self.mode       = mode
        self.setPoint   = setPoint
        self.limitType  = limitType
        self.limit      = limit
