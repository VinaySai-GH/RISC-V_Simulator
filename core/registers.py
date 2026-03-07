class RegisterFile:
    def __init__(self):
        self.registers = [0] * 32

    def read(self, reg_num):
        return self.registers[reg_num]

    def write(self, reg_num, value):
        if reg_num == 0:
            return
        self.registers[reg_num] = value

    def display(self):
        for i, val in enumerate(self.registers):
            if val != 0:              # only show non-zero registers
                print(f"  x{i} = {val}")