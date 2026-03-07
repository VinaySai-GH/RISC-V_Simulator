class ForwardingUnit:
    def __init__(self):
        pass

    def check(self, id_ex, ex_mem, mem_wb):
        """
        Check if values in EX_MEM or MEM_WB can be
        forwarded to the current instruction in ID_EX.
        Returns updated id_ex with correct values.
        """
        if id_ex is None:
            return id_ex, 0   # (instruction, stall_count)

        stalls = 0

        # --- Forward from EX_MEM stage ---
        if ex_mem is not None and "rd" in ex_mem:
            forwarded = self.try_forward(id_ex, ex_mem)
            if forwarded:
                id_ex = forwarded

        # --- Forward from MEM_WB stage ---
        if mem_wb is not None and "rd" in mem_wb:
            forwarded = self.try_forward(id_ex, mem_wb)
            if forwarded:
                id_ex = forwarded

        # --- LW hazard — must stall, can't forward ---
        # LW result only available after Memory stage
        if (ex_mem is not None and
            ex_mem["op"] == "LW" and
            "rd" in ex_mem and
            self.needs_reg(id_ex, ex_mem["rd"])):
            stalls = 1   # insert one bubble

        return id_ex, stalls

    def try_forward(self, id_ex, source):
        """
        If source instruction writes to a register
        that id_ex needs — forward the value.
        """
        if "rd" not in source or "alu_result" not in source:
            return None

        rd  = source["rd"]
        val = source["alu_result"]

        # forward to rs1
        if id_ex.get("rs1") == rd:
            id_ex["rs1_val"] = val

        # forward to rs2
        if id_ex.get("rs2") == rd:
            id_ex["rs2_val"] = val

        return id_ex

    def needs_reg(self, id_ex, rd):
        """Does id_ex need register rd?"""
        return (id_ex.get("rs1") == rd or
                id_ex.get("rs2") == rd)