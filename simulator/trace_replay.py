# simulator/trace_replay.py
import sys
from core.vm import VirtualMemorySystem
from simulator.cache_controller import CacheController
from core.memory import Memory
from core.registers import RegisterFile

class TraceReplayer:
    def __init__(self, trace_file, config):
        self.trace_file = trace_file
        self.config = config
        
        self.memory = Memory(config.get("memory", {}).get("physical_size_bytes", 4096))
        self.registers = RegisterFile()
        self.vm = VirtualMemorySystem(config)
        self.cache_controller = CacheController(config, self.memory)
        
        self.cycles = 0
        self.instructions_executed = 0
        self.stalls = 0

    def get_latency(self, op):
        return self.config.get("latencies", {}).get(op.upper(), 1)

    def parse_reg(self, reg_str):
        reg = reg_str.strip()
        if not reg.startswith("x"):
            raise ValueError(f"Invalid register '{reg_str}': expected x0 through x31")
        try:
            reg_num = int(reg[1:])
        except ValueError:
            raise ValueError(f"Invalid register '{reg_str}': expected x0 through x31")
        if reg_num < 0 or reg_num > 31:
            raise ValueError(f"Invalid register '{reg_str}': expected x0 through x31")
        return reg_num

    def run(self):
        print(f"\n--- Running TRACE REPLAY mode for {self.trace_file} ---\n")
        
        try:
            with open(self.trace_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                        
                    parts = line.split()
                    op = parts[0].upper()
                    base_lat = self.get_latency(op)
                    
                    if op in ["L", "S"]:
                        if len(parts) < 3:
                            print(f"ERROR: Missing address in trace line: {line}")
                            continue
                        try:
                            v_addr = int(parts[1], 16)
                        except ValueError:
                            print(f"ERROR: Invalid hex address '{parts[1]}' in trace line: {line}")
                            continue
                        if v_addr < 0 or v_addr > 0xFFFFFFFF:
                            print(f"ERROR: Virtual address out of range in trace line: {line}")
                            continue
                        try:
                            reg = self.parse_reg(parts[2])
                        except ValueError as exc:
                            print(f"ERROR: {exc} in trace line: {line}")
                            continue
                        is_write = (op == "S")
                        
                        # 1. Virtual Memory Translation (VA -> PA)
                        p_addr, vm_latency = self.vm.translate(v_addr, is_write, self.cycles)
                        
                        # 2. PIPT Cache Access using Physical Address
                        if op == "L":
                            value, cache_latency = self.cache_controller.load_word(p_addr, self.cycles)
                            self.registers.write(reg, value)
                        else:
                            cache_latency = self.cache_controller.store_word(
                                p_addr, self.registers.read(reg), self.cycles
                            )
                        
                        total_latency = vm_latency + cache_latency 
                        
                    elif op in ["ADD", "MUL"]:
                        if len(parts) < 4:
                            print(f"ERROR: Missing register operand in trace line: {line}")
                            continue
                        try:
                            rd = self.parse_reg(parts[1])
                            rs1 = self.parse_reg(parts[2])
                            rs2 = self.parse_reg(parts[3])
                        except ValueError as exc:
                            print(f"ERROR: {exc} in trace line: {line}")
                            continue
                        lhs = self.registers.read(rs1)
                        rhs = self.registers.read(rs2)
                        if op == "ADD":
                            self.registers.write(rd, lhs + rhs)
                        else:
                            self.registers.write(rd, lhs * rhs)
                        total_latency = base_lat
                    else:
                        continue
                    
                    self.cycles += total_latency
                    if total_latency > 1:
                        self.stalls += (total_latency - 1)
                    
                    self.instructions_executed += 1
                    
        except FileNotFoundError:
            print(f"Trace file not found: {self.trace_file}")
            sys.exit(1)
            
        self.print_stats()

    def print_stats(self):
        ipc = self.instructions_executed / self.cycles if self.cycles > 0 else 0
        cache_stats = self.cache_controller.get_stats()
        vm_stats = self.vm.stats
        
        print("\n========== PHASE 3 TRACE RESULTS ==========")
        print(f"Total Cycles              : {self.cycles}")
        print(f"Instructions Executed     : {self.instructions_executed}")
        print(f"IPC                       : {ipc:.4f}")
        print(f"Total Stalls              : {self.stalls}")
        print("-" * 43)
        print("--- Virtual Memory Stats ---")
        print(f"TLB Hits                  : {vm_stats['tlb_hits']}")
        print(f"TLB Misses                : {vm_stats['tlb_misses']}")
        print(f"Page Walks                : {vm_stats['page_walks']}")
        print(f"Page Faults               : {vm_stats['page_faults']}")
        print(f"Page Evictions            : {vm_stats['page_evictions']}")
        print(f"Dirty Evictions/Writebacks: {vm_stats['dirty_evictions']}")
        print(f"Total Translation Penalty : {vm_stats['translation_penalty']} cycles")
        print("-" * 43)
        print("--- Cache Stats ---")
        print(f"L1D Hits                  : {cache_stats['L1D']['hits']}")
        print(f"L1D Misses                : {cache_stats['L1D']['misses']}")
        print("===========================================")
