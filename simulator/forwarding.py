class ForwardingUnit:
    def check(self, id_ex, ex_mem, mem_wb):
        if id_ex is None:
            return id_ex, 0, []

        stalls  = 0
        hazards = []

        # LOAD-USE hazard — must stall (check before forwarding)
        if (ex_mem is not None and
            ex_mem["op"] == "LW" and
            "rd" in ex_mem and
            ex_mem["rd"] != 0 and
            self.needs_reg(id_ex, ex_mem["rd"])):
            stalls = 1
            hazards.append(
                f"LOAD-USE HAZARD: stall inserted — "
                f"LW x{ex_mem['rd']} not ready for {id_ex['op']}"
            )

        # MEM-EX forwarding (older — checked first so EX-EX can override)
        if mem_wb is not None and "rd" in mem_wb and mem_wb["rd"] != 0:
            if self.needs_reg(id_ex, mem_wb["rd"]):
                id_ex = self.try_forward(id_ex, mem_wb)
                hazards.append(
                    f"DATA HAZARD (MEM-EX): forwarded x{mem_wb['rd']} "
                    f"from {mem_wb['op']} -> {id_ex['op']}"
                )

        # EX-EX forwarding (more recent — checked last so it wins)
        if ex_mem is not None and "rd" in ex_mem and ex_mem["rd"] != 0:
            if self.needs_reg(id_ex, ex_mem["rd"]):
                if ex_mem["op"] != "LW":
                    id_ex = self.try_forward(id_ex, ex_mem)
                    hazards.append(
                        f"DATA HAZARD (EX-EX): forwarded x{ex_mem['rd']} "
                        f"from {ex_mem['op']} -> {id_ex['op']}"
                    )

        return id_ex, stalls, hazards

    def try_forward(self, id_ex, source):
        if "rd" not in source:
            return id_ex
        rd = source["rd"]
        # LW in MEM_WB has mem_data (the loaded value); alu_result is just the address
        if source.get("op") == "LW" and "mem_data" in source:
            val = source["mem_data"]
        elif "alu_result" in source:
            val = source["alu_result"]
        else:
            return id_ex
        if id_ex.get("rs1") == rd:
            id_ex["rs1_val"] = val
        if id_ex.get("rs2") == rd:
            id_ex["rs2_val"] = val
        return id_ex

    def needs_reg(self, id_ex, rd):
        return (id_ex.get("rs1") == rd or
                id_ex.get("rs2") == rd)