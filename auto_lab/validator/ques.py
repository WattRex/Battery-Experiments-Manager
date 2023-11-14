#!/usr/bin/python3
import sys, os, csv
sys.path.append(os.getcwd())  #get absolute path

from enum import Enum
from auto_lab.validator.VALIDATOR_ERRORS import VALIDATOR_ErrorCode_e, VALIDATOR_Error_c
from auto_lab.validator.VALIDATOR_POWER import VALIDATOR_Limits_e, VALIDATOR_CylingMode_e, VALIDATOR_Instruction_c

class Crotolamo_c():
    '''
    (old) APP_MAN_CsvInterpreter_c
    '''
    def __init__(self, file):
        self.list = self.__csvToList(file)
    
    def __csvToList(self, file_text : str):
        lines = list(csv.reader(file_text.split('\n'), delimiter=','))
        res = []
        for l in lines:
            newLine = []
            for w in l:
                newLine.append(w.replace(' ', ''))
            res.append(newLine)
        return res

class VALIDATOR_protcol_c ():

    def __existsLimit(self, value):
        return VALIDATOR_Limits_e(value[2]) if value[2] in self.limit._value2member_map_ else False
    def __limitIsFloat(self, value):
        return self.__isFloat(value[1])
    def __refIsFloat(self, value):
        return self.__isFloat(value[3])
    def __isFloat (self, value):
        newValue = False
        try:
            newValue = float(value)
        except ValueError:
            newValue = False
        return newValue

    def checkInstruction(self, instruction : list):
        #check minimum lenght
        if len(instruction) < 2:
            raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_ELEMENTS, str(instruction) + ": Number of elements inconsistent")
        
        #check if mode recognized
        mode = None
        if instruction[0] in VALIDATOR_CylingMode_e._value2member_map_:
            mode = VALIDATOR_CylingMode_e(instruction[0])
        else:
            raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_MODE, str(instruction) + ": Mode not recognized")

        #check ref value
        refValue = None
        if not self.__isFloat(instruction[1]):
            raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_REF, str(instruction) + ": Ref value not recognized") 
        else:
            refValue = int(float(instruction[1])*1000)
            # print('En el interprete leo de refValue: ', refValue)

        #WAIT doesnt require from limit
        if mode == VALIDATOR_CylingMode_e.MODE_WAIT:
            if len(instruction) != 2:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_ELEMENTS, str(instruction) + ": Number of elements inconsistent")
            #check ref value
            if refValue != -1 and refValue < 0:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_REF, str(instruction) + ": Ref value not allowed")
            #set internally the limit mode to TIME
            limitMode = VALIDATOR_Limits_e.LIMIT_TIME
            limitValue = refValue

        elif mode == VALIDATOR_CylingMode_e.MODE_CV:
            if len(instruction) != 4:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_ELEMENTS, str(instruction) + ": Number of elements inconsistent")   
            #check ref value
            if refValue <= 0:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_REF, str(instruction) + ": Ref value not allowed")
            #check limit mode
            limitMode = None
            if instruction[2] in VALIDATOR_Limits_e._value2member_map_:
                limitMode = VALIDATOR_Limits_e(instruction[2])
            else:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_LIMIT, str(instruction) + ": Limit mode not recognized")
            #validate limit mode
            if limitMode == VALIDATOR_Limits_e.LIMIT_VOLTAGE:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_LIMIT, str(instruction) + ": Limit mode not allowed in the selected mode")

        elif mode == VALIDATOR_CylingMode_e.MODE_CC:
            if len(instruction) != 4:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_ELEMENTS, str(instruction) + ": Number of elements inconsistent")
            #not check ref value needed (positive and negative currents allowed)
            #check limit mode
            limitMode = None
            if instruction[2] in VALIDATOR_Limits_e._value2member_map_:
                limitMode = VALIDATOR_Limits_e(instruction[2])
            else:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_LIMIT, str(instruction) + ": Limit mode not recognized")
            #validate limit mode
            if limitMode == VALIDATOR_Limits_e.LIMIT_CURRENT:
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_LIMIT, str(instruction) + ": Limit mode not allowed in the selected mode")
        
        #check limit value for the limit mode selected
        if mode != VALIDATOR_CylingMode_e.MODE_WAIT:
            limitValue = None
            if not self.__isFloat(instruction[3]):
                raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_LIMIT_VAL, str(instruction) + ": Limit value not recognized") 
            else:
                limitValue = int(float(instruction[3])*1000)
            
            #check values depending on limit mode
            if limitMode == VALIDATOR_Limits_e.LIMIT_TIME:
                if limitValue != -1 and limitValue < 0:
                    raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_REF, str(instruction) + ": Limit value not allowed") 
            elif limitMode == VALIDATOR_Limits_e.LIMIT_VOLTAGE:
                if limitValue < 0:
                    raise VALIDATOR_Error_c(VALIDATOR_ErrorCode_e.ERROR_LIMIT_VAL, str(instruction) + ": Limit value not allowed")               
        
        return VALIDATOR_Instruction_c(mode, refValue, limitMode, limitValue)

def permatrago (instructions :list):
    '''
    (old) APP_MAN_validateInstructions
    '''
    outData = []
    for ins in instructions:
        outData.append(VALIDATOR_protcol_c().checkInstruction(ins))
    return outData

