class Memory:
    def __init__(self,size=4096):
        self.memory=[0]*size
        self.size=size

    def load(self,address):
     if address<0 or address+3>=self.size:
        raise Exception(f"Memory access out of bounds: {address}")
     return (self.memory[address] |
                self.memory[address + 1] << 8  |
                self.memory[address + 2] << 16 |
                self.memory[address + 3] << 24)

    def store(self,address,value):
        if address<0 or address+3>=self.size:
            raise Exception(f"Memory access out of bounds:{address}")
        self.memory[address] =value & 0xFF
        self.memory[address+1]=(value >> 8) & 0xFF
        self.memory[address+2]=(value >>16) & 0xFF
        self. memory[address+3]=(value >>24)& 0xFF
             
