class Memory:
    def __init__(self, size=4096):
        self.memory = [0] * size
        self.size   = size

    def load_byte(self, address):
        if address < 0 or address >= self.size:
            raise Exception(f"Memory out of bounds: {address}")
        return self.memory[address]

    def store_byte(self, address, value):
        if address < 0 or address >= self.size:
            raise Exception(f"Memory out of bounds: {address}")
        self.memory[address] = value & 0xFF

    def load(self, address):
        if address < 0 or address + 3 >= self.size:
            raise Exception(f"Memory out of bounds: {address}")
        return (self.memory[address]
                | self.memory[address + 1] << 8
                | self.memory[address + 2] << 16
                | self.memory[address + 3] << 24)

    def store(self, address, value):
        if address < 0 or address + 3 >= self.size:
            raise Exception(f"Memory out of bounds: {address}")
        self.store_byte(address, value)
        self.store_byte(address + 1, value >> 8)
        self.store_byte(address + 2, value >> 16)
        self.store_byte(address + 3, value >> 24)

    def load_block(self, base, block_size):
        if base < 0 or base + block_size > self.size:
            raise Exception(f"Memory block out of bounds: {base}")
        return self.memory[base:base + block_size]

    def store_block(self, base, data):
        if base < 0 or base + len(data) > self.size:
            raise Exception(f"Memory block out of bounds: {base}")
        for offset, value in enumerate(data):
            self.store_byte(base + offset, value)

    def load_array(self, base, values):
        for i, val in enumerate(values):
            self.store(base + i * 4, val)

    def dump_array(self, base, count):
        return [self.load(base + i * 4) for i in range(count)]
