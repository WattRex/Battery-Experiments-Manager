#!/usr/bin/python3
import sys, os, csv
sys.path.append(os.getcwd())  #get absolute path

from typing import Dict, List
from auto_lab.models import Instructions
from auto_lab.models_types import Mode_e, LimitType_e, Mode_Validator_e

class analyzer():
    def __init__(self, instructions: List[Instructions]):
        self.instructions = instructions
        self.curr_max = None
        self.curr_min = None
        self.volt_max = None
        self.volt_min = None
        self.analyze()

    def __str__(self):
        return f" curr_max: {self.curr_max}\n curr_min: {self.curr_min}\n volt_max: {self.volt_max}\n volt_min: {self.volt_min}"

    def analyze(self):
        for instruction in self.instructions:
            if instruction.mode == Mode_e.CC_MODE:
                if self.curr_max != None:
                    if instruction.set_point > self.curr_max:
                        self.curr_max = instruction.set_point
                    elif instruction.set_point < self.curr_min:
                        self.curr_min = instruction.set_point
                else:
                    self.curr_max = instruction.set_point
                    self.curr_min = instruction.set_point
                if instruction.limit_type == LimitType_e.VOLTAGE:
                    if self.volt_max != None:
                        if instruction.limit_point > self.volt_max:
                            self.volt_max = instruction.limit_point
                        elif instruction.limit_point < self.volt_min:
                            self.volt_min = instruction.limit_point
                    else:
                        self.volt_max = instruction.limit_point
                        self.volt_min = instruction.limit_point

            elif instruction.mode == Mode_e.CV_MODE:
                if self.volt_max != None:
                    if instruction.set_point > self.volt_max:
                        self.volt_max = instruction.set_point
                    elif instruction.set_point < self.volt_min:
                        self.volt_min = instruction.set_point
                else:
                    self.volt_max = instruction.set_point
                    self.volt_min = instruction.set_point
                if instruction.limit_type == LimitType_e.CURRENT:
                    if self.curr_max != None:
                        if instruction.limit_point > self.curr_max:
                            self.curr_max = instruction.limit_point
                        elif instruction.limit_point < self.curr_min:
                            self.curr_min = instruction.limit_point
                    else:
                        self.curr_max = instruction.limit_point
                        self.curr_min = instruction.limit_point
        if self.curr_max == None:
            self.curr_max = 0
            self.curr_min = 0


def stringToInstructions(raw_text : str) -> List[Instructions]:
    raw_text = raw_text.replace('\r\n', '\n')
    raw_list = raw_text.split('\n')
    instructions = []
    instruction_index = 1
    for line in raw_list:
        if line != '':
            line_split = line.split(', ')
            if line_split[0] == Mode_e.WAIT.value:
                instructions.append(Instructions(instr_id = instruction_index, mode=Mode_e.WAIT, set_point=int(float(line_split[1])*1000), limit_type=LimitType_e.TIME, limit_point=int(float(line_split[1])*1000)))
            else:
                instructions.append(Instructions(instr_id = instruction_index, mode=Mode_e(Mode_Validator_e(line_split[0]).name), set_point=int(float(line_split[1])*1000), limit_type=LimitType_e(line_split[2]), limit_point=int(float(line_split[3])*1000)))
            instruction_index += 1
    
    return instructions







