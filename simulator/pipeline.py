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

        self.memory.load_array(0, [5, 3, 8, 1, 2])

        self.pc              = 0
        self.cycles          = 0
        self.stalls          = 0
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
            raw = fetch(self.instructions, self.pc)
            if raw is None:
                break
            decoded   = decode(raw)
            decoded   = self.decoder.fill_values(
                decoded, self.registers, self.labels)
            if decoded["op"] == "JAL":
                decoded["pc_plus_4"] = (self.pc + 1) * 4
            executed  = execute(decoded)
            after_mem = memory_access(executed, self.memory)
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
            MEM_WB,m_lat=memory_access(EX_MEM,self.memory,self.cache_controller,self.cycles) if EX_MEM is not None else None
            if m_lat>1:
                penalty=m_lat-1
                self.stalls+=penalty
                self.cycles+=penalty
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
                ID_EX = decode(IF_ID)
                if ID_EX is not None:
                    ID_EX = self.decoder.fill_values(
                        ID_EX, self.registers, self.labels)
                    if ID_EX["op"] == "JAL":
                        ID_EX["pc_plus_4"] = self.pc * 4
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
            raw,f_lat = fetch(self.instructions, self.pc,self.cache_controller,self.cycles)

            IF_ID = raw
            if raw is not None:
                self.pc += 1
                IF_ID = raw
            if f_lat > 1:
                penalty = f_lat - 1
                self.stalls += penalty
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
                    if target >= len(self.instructions):
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
            raw = fetch(self.instructions, self.pc)
            if raw is None:
                break

            decoded = decode(raw)
            decoded = self.decoder.fill_values(
                decoded, self.registers, self.labels)
            if decoded["op"] == "JAL":
                decoded["pc_plus_4"] = (self.pc + 1) * 4

            # detect hazards vs previous 2 instructions
            # check dist-1 first (bigger stall)
            if prev_1 is not None:
                hazards = self.detect_hazards_no_fwd(decoded, prev_1, distance=1)
                for h in hazards:
                    self.hazard_log.append(h)
                    self.stalls += 2
                    self.cycles += 2

            # check dist-2 (only if dist-1 didn't already cover that register)
            if prev_2 is not None:
                hazards = self.detect_hazards_no_fwd(decoded, prev_2, distance=2)
                for h in hazards:
                    self.hazard_log.append(h)
                    self.stalls += 1
                    self.cycles += 1

            executed  = execute(decoded)
            after_mem = memory_access(executed, self.memory)
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
            if decoded["target_pc"] >= len(self.instructions):
                return len(self.instructions)
            return decoded["target_pc"]
        return None

    def print_stats(self):
        ipc = self.instr_completed / self.cycles if self.cycles > 0 else 0
        print(f"Final IPC: {ipc:.4f}")
        evel
        for cache in [self.cache_controller.l1i, self.cache_controller.l1d, self.cache_controller.l2]:
                total = cache.hits + cache.misses
                rate = (cache.misses / total) * 100 if total > 0 else 0
                print(f"{cache.name} Miss Rate: {rate:.2f}%")
        print("\n========== RESULTS ==========")
        print(f"Instructions completed : {self.instr_completed}")
        print(f"Total cycles           : {self.cycles}")
        print(f"Stalls                 : {self.stalls}")
        print(f"IPC                    : {ipc:.2f}")
        print("=============================")
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