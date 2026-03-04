from core.registers import RegisterFile
from core.memory import Memory
from core.decoder import Decoder
from utils.assembler import Assembler
from simulator.stages import fetch, decode, execute, memory_access, writeback

class Pipeline:
    def __init__(self, instructions, labels, use_pipeline, use_forwarding, config):
        self.instructions    = instructions
        self.labels          = labels
        self.use_pipeline    = use_pipeline
        self.use_forwarding  = use_forwarding
        self.config          = config

        self.registers = RegisterFile()
        self.memory    = Memory()
        self.decoder   = Decoder()

        self.pc        = 0
        self.cycles    = 0
        self.stalls    = 0
        self.instr_completed = 0

    def run(self):
        if self.use_pipeline:
            self.run_pipelined()
        else:
            self.run_simple()

        self.print_stats()

    # ----------------------------------------------------------
    # SIMPLE MODE — no pipeline, one instruction at a time
    # ----------------------------------------------------------
    def run_simple(self):
        print("\n--- Running in SIMPLE (non-pipelined) mode ---\n")

        while self.pc < len(self.instructions):
            raw = fetch(self.instructions, self.pc)
            if raw is None:
                break

            decoded = decode(raw)
            if decoded is None:
                break

            # fill in register values
            decoded = self.decoder.fill_values(decoded, self.registers, self.labels)

            executed  = execute(decoded)
            after_mem = memory_access(executed, self.memory)
            writeback(after_mem, self.registers)

            # handle branches and jumps
            self.pc = self.handle_pc(after_mem)

            self.cycles += 5   # each instruction takes 5 cycles (one per stage)
            self.instr_completed += 1

    # ----------------------------------------------------------
    # PIPELINED MODE
    # ----------------------------------------------------------
    def run_pipelined(self):
        print("\n--- Running in PIPELINED mode ---\n")

        # 5 pipeline registers (slots), start empty
        IF_ID  = None
        ID_EX  = None
        EX_MEM = None
        MEM_WB = None

        while True:
            # --- Writeback ---
            writeback(MEM_WB, self.registers)
            if MEM_WB is not None:
                self.instr_completed += 1

            # --- Memory ---
            MEM_WB = memory_access(EX_MEM, self.memory)

            # --- Execute ---
            EX_MEM = execute(ID_EX)

            # --- Decode ---
            if IF_ID is not None:
                ID_EX = decode(IF_ID)
                if ID_EX is not None:
                    ID_EX = self.decoder.fill_values(ID_EX, self.registers, self.labels)
            else:
                ID_EX = None

            # --- Fetch ---
            raw   = fetch(self.instructions, self.pc)
            IF_ID = raw

            # advance PC
            if raw is not None:
                self.pc += 1

            # handle branch/jump from EX_MEM stage
            if EX_MEM is not None:
                new_pc = self.handle_pc(EX_MEM)
                if new_pc != self.pc:
                    self.pc = new_pc
                    IF_ID  = None   # flush wrong instructions
                    ID_EX  = None

            self.cycles += 1

            # stop when pipeline is fully drained
            if (raw is None and IF_ID is None and
                ID_EX is None and EX_MEM is None and MEM_WB is None):
                break

    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------
    def handle_pc(self, decoded):
        """Returns next PC — handles branches and jumps"""
        if decoded is None:
            return self.pc

        if decoded["op"] == "BNE" and decoded["alu_result"] == 1:
            return decoded["target_pc"]   # branch taken

        if decoded["op"] == "JAL":
            return decoded["target_pc"]   # always jump

        return self.pc + (0 if self.use_pipeline else 1)

    def print_stats(self):
        ipc = self.instr_completed / self.cycles if self.cycles > 0 else 0
        print("\n========== RESULTS ==========")
        print(f"Instructions completed : {self.instr_completed}")
        print(f"Total cycles           : {self.cycles}")
        print(f"Stalls                 : {self.stalls}")
        print(f"IPC                    : {ipc:.2f}")
        print("=============================")
        print("\nFinal Register State:")
        self.registers.display()