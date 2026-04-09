import math
import random


class CacheLine:
    def __init__(self, block_size):
        self.valid = False
        self.tag = None
        self.last_used = 0
        self.inserted_at = 0
        self.block_base = 0
        self.dirty = False
        self.data = bytearray(block_size)


class CacheLevel:
    def __init__(self, name, size, block_size, associativity, latency, policy="LRU"):
        self.name = name
        self.size = size
        self.block_size = block_size
        self.associativity = associativity
        self.latency = latency
        self.policy = policy.upper()

        self.num_sets = size // (block_size * associativity)
        if self.num_sets <= 0:
            raise ValueError(f"{name}: invalid cache configuration")
        if block_size & (block_size - 1):
            raise ValueError(f"{name}: block_size must be a power of two")
        if self.num_sets & (self.num_sets - 1):
            raise ValueError(f"{name}: num_sets must be a power of two")

        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(self.num_sets))

        self.sets = [
            [CacheLine(block_size) for _ in range(associativity)]
            for _ in range(self.num_sets)
        ]

        self.hits = 0
        self.misses = 0

    def _get_parts(self, address):
        index = (address >> self.offset_bits) & (self.num_sets - 1)
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index

    def _block_base(self, address):
        return address - (address % self.block_size)

    def _offset(self, address):
        return address % self.block_size

    def _find_line(self, address):
        tag, index = self._get_parts(address)
        target_set = self.sets[index]

        for line in target_set:
            if line.valid and line.tag == tag:
                return line

        return None

    def access(self, address, current_cycle):
        line = self._find_line(address)
        if line is not None:
            self.hits += 1
            line.last_used = current_cycle
            return True

        self.misses += 1
        return False

    def allocate_line(self, address, block_data, current_cycle):
        tag, index = self._get_parts(address)
        target_set = self.sets[index]

        for line in target_set:
            if not line.valid:
                self._fill_line(
                    line, tag, self._block_base(address), block_data, current_cycle
                )
                return None

        victim = self._choose_victim(target_set)
        evicted = None
        if victim.valid and victim.dirty:
            evicted = {
                "base": victim.block_base,
                "data": bytes(victim.data),
            }

        self._fill_line(victim, tag, self._block_base(address), block_data, current_cycle)
        return evicted

    def read_word(self, address, current_cycle):
        line = self._find_line(address)
        if line is None:
            raise KeyError(f"{self.name}: cache read miss at {address}")
        line.last_used = current_cycle
        offset = self._offset(address)
        if offset + 4 > self.block_size:
            raise ValueError(f"{self.name}: unaligned block read at {address}")
        data = line.data
        return (data[offset]
                | data[offset + 1] << 8
                | data[offset + 2] << 16
                | data[offset + 3] << 24)

    def write_word(self, address, value, current_cycle):
        line = self._find_line(address)
        if line is None:
            raise KeyError(f"{self.name}: cache write miss at {address}")
        line.last_used = current_cycle
        offset = self._offset(address)
        if offset + 4 > self.block_size:
            raise ValueError(f"{self.name}: unaligned block write at {address}")
        line.data[offset] = value & 0xFF
        line.data[offset + 1] = (value >> 8) & 0xFF
        line.data[offset + 2] = (value >> 16) & 0xFF
        line.data[offset + 3] = (value >> 24) & 0xFF
        line.dirty = True

    def write_block(self, address, block_data, current_cycle, dirty=False):
        line = self._find_line(address)
        if line is None:
            evicted = self.allocate_line(address, block_data, current_cycle)
            line = self._find_line(address)
        else:
            evicted = None
            line.data[:] = bytes(block_data)
            line.last_used = current_cycle
        line.dirty = dirty
        return evicted

    def dirty_blocks(self):
        blocks = []
        for target_set in self.sets:
            for line in target_set:
                if line.valid and line.dirty:
                    blocks.append({
                        "base": line.block_base,
                        "data": bytes(line.data),
                    })
                    line.dirty = False
        return blocks

    def _choose_victim(self, target_set):
        if self.policy == "LRU":
            return min(target_set, key=lambda line: line.last_used)
        if self.policy == "FIFO":
            return min(target_set, key=lambda line: line.inserted_at)
        return random.choice(target_set)

    def _fill_line(self, line, tag, block_base, block_data, current_cycle):
        line.valid = True
        line.tag = tag
        line.last_used = current_cycle
        line.inserted_at = current_cycle
        line.block_base = block_base
        line.dirty = False
        line.data[:] = bytes(block_data)
