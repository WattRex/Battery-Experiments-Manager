#!/usr/bin/python3

from enum import Enum

class VALIDATOR_ErrorCode_e (Enum):
    ERROR_ELEMENTS  = 0
    ERROR_MODE      = 1
    ERROR_REF       = 2
    ERROR_LIMIT     = 3
    ERROR_LIMIT_VAL = 4
    MODE_COUNT      = 5

class VALIDATOR_Error_c(Exception):
    """Exception raised for errors when an input not found in the database.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, code : VALIDATOR_ErrorCode_e, message):
        super().__init__(message)
        self.errCode = code