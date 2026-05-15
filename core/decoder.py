class Decoder:
    def decode(self, instruction):
        op       = instruction["op"]
        operands = instruction["operands"]

        if op in ("ADD", "SUB", "AND", "OR", "SLT", "MUL"):
            return {
                "op"  : op,
                "type": "R",
                "rd"  : self.parse_reg(operands[0]),
                "rs1" : self.parse_reg(operands[1]),
                "rs2" : self.parse_reg(operands[2]),
            }

        elif op == "ADDI":
            # Sign-extend 12-bit immediate to 32-bit
            offset = int(operands[2])
            if offset >= 2048:
                offset -= 4096
            return {
                "op"    : op,
                "type"  : "I",
                "rd"    : self.parse_reg(operands[0]),
                "rs1"   : self.parse_reg(operands[1]),
                "offset": offset,
            }

        elif op == "LW":
            rd, offset, rs1 = self.parse_mem_operand(operands)
            return {
                "op"    : op,
                "type"  : "I",
                "rd"    : rd,
                "rs1"   : rs1,
                "offset": offset,
            }

        elif op == "SW":
            rs2, offset, rs1 = self.parse_mem_operand(operands)
            return {
                "op"    : op,
                "type"  : "S",
                "rs1"   : rs1,
                "rs2"   : rs2,
                "offset": offset,
            }

        elif op == "BNE":
            return {
                "op"   : op,
                "type" : "B",
                "rs1"  : self.parse_reg(operands[0]),
                "rs2"  : self.parse_reg(operands[1]),
                "label": operands[2],
            }

        elif op == "JAL":
            return {
                "op"      : op,
                "type"    : "J",
                "rd"      : self.parse_reg(operands[0]),
                "label"   : operands[1],
                "pc_plus_4": 0,   # filled by pipeline
            }

        else:
            raise Exception(f"Unknown instruction: {op}")

    def fill_values(self, decoded, registers, labels):
        if "rs1" in decoded:
            decoded["rs1_val"] = registers.read(decoded["rs1"])
        if "rs2" in decoded:
            decoded["rs2_val"] = registers.read(decoded["rs2"])
        if "label" in decoded:
            decoded["target_pc"] = labels[decoded["label"]]
        return decoded

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

    def parse_mem_operand(self, operands):
        reg1 = self.parse_reg(operands[0])
        offset_str, reg_str = operands[1].replace(")", "").split("(")
        reg2   = self.parse_reg(reg_str)
        # Sign-extend 12-bit offset to 32-bit (standard RISC-V immediate)
        offset = int(offset_str)
        if offset >= 2048:  # If bit 11 is set (0x800 = 2048)
            offset -= 4096   # Convert to negative (two's complement)
        return reg1, offset, reg2
