from core.registers import RegisterFile
from core.memory import Memory
from core.decoder import Decoder
from simulator.stages import fetch, decode, execute, memory_access, writeback
from simulator.forwarding import ForwardingUnit

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
            decoded   = self.decoder.fill_values(decoded, self.registers, self.labels)
            executed  = execute(decoded)
            after_mem = memory_access(executed, self.memory)
            writeback(after_mem, self.registers)

            next_pc = self.handle_pc(after_mem)
            self.pc = next_pc if next_pc != self.pc else self.pc + 1

            self.cycles          += 5
            self.instr_completed += 1
            count += 1

    def run_pipelined(self):
        print("\n--- Running in PIPELINED mode ---\n")

        IF_ID  = None
        ID_EX  = None
        EX_MEM = None
        MEM_WB = None
        max_cycles = 50000

        while self.cycles < max_cycles:

            # ── WRITEBACK ──────────────────────────────
            writeback(MEM_WB, self.registers)
            if MEM_WB is not None:
                self.instr_completed += 1

            # ── MEMORY ────────────────────────────────
            MEM_WB = memory_access(EX_MEM, self.memory)

            # ── EXECUTE ───────────────────────────────
            EX_MEM = execute(ID_EX)

            # ── DECODE ────────────────────────────────
            if IF_ID is not None:
                ID_EX = decode(IF_ID)
                if ID_EX is not None:
                    ID_EX = self.decoder.fill_values(
                        ID_EX, self.registers, self.labels)
            else:
                ID_EX = None

            # ── FORWARDING / STALL ────────────────────
            if ID_EX is not None:
                if self.use_forwarding:
                    ID_EX, stall_count, hazards = self.forwarding_unit.check(
                        ID_EX, EX_MEM, MEM_WB)
                    self.hazard_log.extend(hazards)
                else:
                    stall_count = self.forwarding_unit.stall_only(
                        ID_EX, EX_MEM, MEM_WB)
                if stall_count > 0:
                    self.stalls += stall_count
                    self.cycles += stall_count
                    ID_EX   = None
                    self.pc -= 1

            # ── FETCH ─────────────────────────────────
            raw   = fetch(self.instructions, self.pc)
            IF_ID = raw
            if raw is not None:
                self.pc += 1

            # ── BRANCH RESOLUTION ─────────────────────
            if EX_MEM is not None:
                if EX_MEM["op"] == "BNE" and EX_MEM["alu_result"] == 1:
                    target = EX_MEM["target_pc"]
                    self.pc = target
                    IF_ID   = None
                    ID_EX   = None
                elif EX_MEM["op"] == "JAL":
                    target = EX_MEM["target_pc"]
                    if target >= len(self.instructions) - 1:
                        self.pc = len(self.instructions)
                    else:
                        self.pc = target
                    IF_ID   = None
                    ID_EX   = None

            self.cycles += 1

            # stop when fully drained
            if (IF_ID is None and ID_EX is None and
                EX_MEM is None and MEM_WB is None and
                self.pc >= len(self.instructions)):
                break

    def handle_pc(self, decoded):
        """Returns next PC — handles branches and jumps (simple mode only)"""
        if decoded is None:
            return self.pc

        if decoded["op"] == "BNE" and decoded["alu_result"] == 1:
            return decoded["target_pc"]

        if decoded["op"] == "JAL":
            if decoded["target_pc"] >= len(self.instructions) - 1:
                return len(self.instructions)
            return decoded["target_pc"]

        return self.pc

    def print_stats(self):
        ipc = self.instr_completed / self.cycles if self.cycles > 0 else 0
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