from core.cache import CacheLevel


class CacheController:
    def __init__(self, config, memory=None):
        cache_config = config["cache"]
        policy = cache_config["replacement_policy"]
        self.memory_latency = cache_config["memory_latency"]
        self.memory = memory

        self.l1i = CacheLevel("L1I", **cache_config["L1I"], policy=policy)
        self.l1d = CacheLevel("L1D", **cache_config["L1D"], policy=policy)
        self.l2 = CacheLevel("L2", **cache_config["L2"], policy=policy)

    def fetch_instruction(self, address, cycle):
        return self._access_hierarchy(address, self.l1i, cycle)

    def load_word(self, address, cycle):
        latency = self._access_data_hierarchy(address, cycle)
        return self.l1d.read_word(address, cycle), latency

    def store_word(self, address, value, cycle):
        latency = self._access_data_hierarchy(address, cycle)
        self.l1d.write_word(address, value, cycle)
        self.l2.write_word(address, value, cycle)
        return latency

    def _access_hierarchy(self, address, l1_cache, cycle):
        total_latency = 0

        total_latency += l1_cache.latency
        if l1_cache.access(address, cycle):
            return total_latency

        total_latency += self.l2.latency
        if self.l2.access(address, cycle):
            block_data = self._read_block_from_l2(address)
            evicted = l1_cache.allocate_line(address, block_data, cycle)
            self._write_back_to_l2(evicted, cycle)
            return total_latency

        total_latency += self.memory_latency
        block_data = self._read_block_from_memory(address, self.l2.block_size)
        evicted = self.l2.allocate_line(address, block_data, cycle)
        self._write_back_to_memory(evicted)

        block_data = self._read_block_from_l2(address)
        evicted = l1_cache.allocate_line(address, block_data, cycle)
        self._write_back_to_l2(evicted, cycle)
        return total_latency

    def _access_data_hierarchy(self, address, cycle):
        return self._access_hierarchy(address, self.l1d, cycle)

    def _block_base(self, address, block_size):
        return address - (address % block_size)

    def _read_block_from_memory(self, address, block_size):
        if self.memory is None:
            return bytes(block_size)
        block_base = self._block_base(address, block_size)
        return bytes(self.memory.load_block(block_base, block_size))

    def _read_block_from_l2(self, address):
        block_base = self._block_base(address, self.l1d.block_size)
        data = bytearray(self.l1d.block_size)
        for offset in range(0, self.l1d.block_size, 4):
            word = self.l2.read_word(block_base + offset, 0)
            data[offset] = word & 0xFF
            data[offset + 1] = (word >> 8) & 0xFF
            data[offset + 2] = (word >> 16) & 0xFF
            data[offset + 3] = (word >> 24) & 0xFF
        return bytes(data)

    def _write_back_to_l2(self, evicted, cycle):
        if evicted is None:
            return
        lower_evicted = self.l2.write_block(evicted["base"], evicted["data"], cycle, dirty=True)
        self._write_back_to_memory(lower_evicted)

    def _write_back_to_memory(self, evicted):
        if evicted is None:
            return
        if self.memory is not None:
            self.memory.store_block(evicted["base"], evicted["data"])

    def get_stats(self):
        return {
            "L1I": {"hits": self.l1i.hits, "misses": self.l1i.misses},
            "L1D": {"hits": self.l1d.hits, "misses": self.l1d.misses},
            "L2": {"hits": self.l2.hits, "misses": self.l2.misses},
        }

    def flush(self):
        for block in self.l1d.dirty_blocks():
            lower_evicted = self.l2.write_block(block["base"], block["data"], 0, dirty=True)
            self._write_back_to_memory(lower_evicted)
        for block in self.l2.dirty_blocks():
            self._write_back_to_memory(block)
