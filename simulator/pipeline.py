from core.registers import RegisterFile
from core.memory import Memory
from core.decoder import Decoder
from simulator.stages import fetch, decode, execute, memory_access, writeback
from simulator.forwarding import ForwardingUnit
from simulator.cache_controller import CacheController

class Pipeline:
    def __init__(self, instructions, labels, use_pipeline, use_forwarding, config):
        self.instructions    = instructions
        self.labels          = labels
        self.use_pipeline    = use_pipeline
        self.use_forwarding  = use_forwarding
        self.config          = config

        self.registers       = RegisterFile()
        self.memory          = Memory()
        self.decoder         = Decoder()
        self.forwarding_unit = ForwardingUnit()
        self.cache_controller = CacheController(config, self.memory)

        self.memory.load_array(0, [5, 3, 8, 1, 2])

        self.pc              = 0
        self.cycles          = 0
        self.stalls          = 0
        self.cache_stalls    = 0
        self.instr_completed = 0
        self.hazard_log      = []

    def get_latency(self, op):
        latencies = self.config.get("latencies", {})
        return latencies.get(op, 1)

    def run(self):
        if self.use_pipeline:
            self.run_pipelined()
        else:
            self.run_simple()
        self.print_stats()

    def run_simple(self):
        print("\n--- Running in SIMPLE (non-pipelined) mode ---\n")
        count = 0
        max_instructions = 10000
        while self.pc < len(self.instructions) and count < max_instructions:
            current_pc = self.pc
            raw, fetch_latency = fetch(
                self.instructions, self.pc, self.cache_controller, self.cycles
            )
            if raw is None:
                break
            if fetch_latency > 1:
                extra = fetch_latency - 1
                self.stalls += extra
                self.cache_stalls += extra
                self.cycles += extra
            decoded   = decode(raw)
            decoded   = self.decoder.fill_values(
                decoded, self.registers, self.labels)
            decoded["pc_index"] = current_pc
            if decoded["op"] == "JAL":
                decoded["pc_plus_4"] = (current_pc + 1) * 4
            executed  = execute(decoded)
            after_mem, mem_latency = memory_access(
                executed, self.memory, self.cache_controller, self.cycles
            )
            if mem_latency > 1:
                extra = mem_latency - 1
                self.stalls += extra
                self.cache_stalls += extra
                self.cycles += extra
            writeback(after_mem, self.registers)
            next_pc   = self.handle_pc(after_mem)
            if next_pc is not None:
                self.pc = next_pc
            else:
                self.pc += 1
            self.cycles          += 5
            self.instr_completed += 1
            count += 1

    def run_pipelined(self):
        print("\n--- Running in PIPELINED mode ---\n")

        if not self.use_forwarding:
            self.run_pipelined_no_forwarding()
            return

        IF_ID  = None
        ID_EX  = None
        EX_MEM = None
        MEM_WB = None
        max_cycles = 50000

        while self.cycles < max_cycles:

            # WRITEBACK
            writeback(MEM_WB, self.registers)
            if MEM_WB is not None:
                self.instr_completed += 1

            # MEMORY
            if EX_MEM is not None:
                mem_input = EX_MEM.copy()
                MEM_WB, m_lat = memory_access(
                    mem_input, self.memory, self.cache_controller, self.cycles
                )
            else:
                MEM_WB, m_lat = None, 0

            if m_lat > 1:
                penalty = m_lat - 1
                self.stalls += penalty
                self.cache_stalls += penalty
                self.cycles += penalty
            # EXECUTE
            EX_MEM = execute(ID_EX.copy()) if ID_EX is not None else None

            # latency stalls
            if EX_MEM is not None:
                latency = self.get_latency(EX_MEM["op"])
                if latency > 1:
                    extra = latency - 1
                    self.stalls += extra
                    self.cycles += extra
                    self.hazard_log.append(
                        f"LATENCY STALL: {EX_MEM['op']} "
                        f"latency={latency} -> {extra} extra stall(s)"
                    )

            # DECODE
            if IF_ID is not None:
                ID_EX = decode(IF_ID["raw"])
                if ID_EX is not None:
                    ID_EX = self.decoder.fill_values(
                        ID_EX, self.registers, self.labels)
                    ID_EX["pc_index"] = IF_ID["pc"]
                    if ID_EX["op"] == "JAL":
                        ID_EX["pc_plus_4"] = (IF_ID["pc"] + 1) * 4
            else:
                ID_EX = None

            # FORWARDING + HAZARD DETECTION
            if ID_EX is not None:
                ID_EX, stall_count, hazards = self.forwarding_unit.check(
                    ID_EX, EX_MEM, MEM_WB)
                self.hazard_log.extend(hazards)
                if stall_count > 0:
                    self.stalls += stall_count
                    self.cycles += stall_count
                    ID_EX   = None
                    self.pc -= 1

            # FETCH
            fetch_pc = self.pc
            raw, f_lat = fetch(
                self.instructions, self.pc, self.cache_controller, self.cycles
            )

            IF_ID = {"raw": raw, "pc": fetch_pc} if raw is not None else None
            if raw is not None:
                self.pc += 1
            if f_lat > 1:
                penalty = f_lat - 1
                self.stalls += penalty
                self.cache_stalls += penalty
                self.cycles += penalty

            # BRANCH RESOLUTION
            if EX_MEM is not None:
                if EX_MEM["op"] == "BNE" and EX_MEM["alu_result"] == 1:
                    target = EX_MEM["target_pc"]
                    self.pc = target
                    IF_ID   = None
                    ID_EX   = None
                    self.stalls += 2
                    self.cycles += 2
                    self.hazard_log.append(
                        f"CONTROL HAZARD: BNE taken -> "
                        f"flushed 2 instructions, "
                        f"jumped to line {target}"
                    )
                elif EX_MEM["op"] == "JAL":
                    target = EX_MEM["target_pc"]
                    if target == EX_MEM.get("pc_index"):
                        self.pc = len(self.instructions)
                        IF_ID = None
                        ID_EX = None
                    elif target >= len(self.instructions):
                        self.pc = len(self.instructions)
                        IF_ID = None
                        ID_EX = None
                    else:
                        self.pc  = target
                        IF_ID    = None
                        ID_EX    = None
                        self.stalls += 2
                        self.cycles += 2
                        self.hazard_log.append(
                            f"CONTROL HAZARD: JAL taken -> "
                            f"flushed 2 instructions, "
                            f"jumped to line {target}"
                        )

            self.cycles += 1

            if (IF_ID is None and ID_EX is None and
                EX_MEM is None and MEM_WB is None and
                self.pc >= len(self.instructions)):
                break

    def run_pipelined_no_forwarding(self):
        """
        No forwarding mode — execute correctly like simple mode
        but count stalls and hazards for pipeline overhead.
        Without forwarding, results are only available after WB, so:
          - Distance-1 hazard (immediately previous instr) -> 2 stalls
          - Distance-2 hazard (two instructions back)      -> 1 stall
        """
        count = 0
        max_instructions = 10000
        prev_1 = None  # immediately previous instruction
        prev_2 = None  # two instructions back

        while self.pc < len(self.instructions) and count < max_instructions:
            current_pc = self.pc
            raw, fetch_latency = fetch(
                self.instructions, self.pc, self.cache_controller, self.cycles
            )
            if raw is None:
                break
            if fetch_latency > 1:
                extra = fetch_latency - 1
                self.stalls += extra
                self.cache_stalls += extra
                self.cycles += extra

            decoded = decode(raw)
            decoded = self.decoder.fill_values(
                decoded, self.registers, self.labels)
            decoded["pc_index"] = current_pc
            if decoded["op"] == "JAL":
                decoded["pc_plus_4"] = (current_pc + 1) * 4

            # detect hazards vs previous 2 instructions
            # check dist-1 first (bigger stall)
            if prev_1 is not None:
                hazards = self.detect_hazards_no_fwd(decoded, prev_1, distance=1)
                if hazards:
                    self.hazard_log.extend(hazards)
                    self.stalls += 2
                    self.cycles += 2

            # check dist-2 (only if dist-1 didn't already cover that register)
            if prev_2 is not None:
                hazards = self.detect_hazards_no_fwd(decoded, prev_2, distance=2)
                if hazards:
                    self.hazard_log.extend(hazards)
                    self.stalls += 1
                    self.cycles += 1

            executed  = execute(decoded)
            after_mem, mem_latency = memory_access(
                executed, self.memory, self.cache_controller, self.cycles
            )
            if mem_latency > 1:
                extra = mem_latency - 1
                self.stalls += extra
                self.cache_stalls += extra
                self.cycles += extra
            writeback(after_mem, self.registers)

            next_pc = self.handle_pc(after_mem)

            # control hazard
            if after_mem["op"] in ("BNE", "JAL") and next_pc is not None:
                self.stalls += 2
                self.cycles += 2
                self.hazard_log.append(
                    f"CONTROL HAZARD: {after_mem['op']} taken -> "
                    f"flushed 2 instructions, jumped to line {next_pc}"
                )
                # pipeline is flushed after branch — reset history
                prev_1 = None
                prev_2 = None
                self.pc = next_pc
            else:
                prev_2 = prev_1
                prev_1 = after_mem
                self.pc += 1

            self.cycles          += 1
            self.instr_completed += 1
            count += 1

    def detect_hazards_no_fwd(self, current, prev, distance=1):
        """Detect RAW hazards between current and a previous instruction"""
        hazards = []
        if "rd" not in prev or prev["rd"] == 0:
            return hazards
        rd = prev["rd"]
        if current.get("rs1") == rd:
            hazards.append(
                f"DATA HAZARD: STALL(no-fwd, dist={distance}) x{rd} "
                f"from {prev['op']} -> {current['op']}"
            )
        if current.get("rs2") == rd:
            hazards.append(
                f"DATA HAZARD: STALL(no-fwd, dist={distance}) x{rd} "
                f"from {prev['op']} -> {current['op']} (rs2)"
            )
        return hazards

    def handle_pc(self, decoded):
        if decoded is None:
            return None
        if decoded["op"] == "BNE" and decoded["alu_result"] == 1:
            return decoded["target_pc"]
        if decoded["op"] == "JAL":
            if decoded.get("target_pc") == decoded.get("pc_index"):
                return len(self.instructions)
            if decoded["target_pc"] >= len(self.instructions):
                return len(self.instructions)
            return decoded["target_pc"]
        return None

    def print_stats(self):
        self.cache_controller.flush()
        ipc = self.instr_completed / self.cycles if self.cycles > 0 else 0
        cache_stats = self.cache_controller.get_stats()

        print("\n========== RESULTS ==========")
        print(f"Instructions completed : {self.instr_completed}")
        print(f"Total cycles           : {self.cycles}")
        print(f"Total stalls           : {self.stalls}")
        print(f"Cache stalls           : {self.cache_stalls}")
        print(f"IPC                    : {ipc:.4f}")
        print("=============================")

        print("\n--- Cache Performance ---")
        for cache_name, data in cache_stats.items():
            hits = data["hits"]
            misses = data["misses"]
            accesses = hits + misses
            miss_rate = (misses / accesses) * 100 if accesses > 0 else 0

            print(f"{cache_name} Hits      : {hits}")
            print(f"{cache_name} Misses    : {misses}")
            print(f"{cache_name} Miss Rate : {miss_rate:.2f}%")

        print("\n--- Hazards Detected ---")
        if self.hazard_log:
            for h in self.hazard_log:
                print(f"  {h}")
        else:
            print("  None")
        print("\nFinal Register State (non-zero only):")
        self.registers.display()
        print("\nSorted Array:")
        print(self.memory.dump_array(0, 5))
