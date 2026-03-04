class Decode:
    def decode(self,instruction):
       
        op=instruction["op"]
        operands=instruction["operands"]

        if op in ("ADD","SUB"):
            return {
                "op":op,
                "type":"R",
                "rd": self.parse_reg(operands[0]),
                "rs1" : self.parse_reg(operands[1]),
                "rs2":self.parse_reg(operands[2])
           }

        elif op=="LW":
            
                rd,offset,rs1=self.parse_mem_operand(operands)
                return {
                "op":op,
                "type":"I",
                "rd":rd,
                "rs1":rs1,
                "offset":offset,
                }
            
        elif op=="SW":
               rs2,offset,rs1=self.parse_mem_operand(operands)
               return{
                "op" : op,
                "type":"S",
                "rs1":rs1,
                "rs2":rs2,
                "offset":offset,
               }

        elif op=="JAL":
                   return{
                    "op":op,
                    "type":"J",
                    "rd":self.parse_reg(operands[0]),
                    "label":operands[1],
                   }
        else:
                    raise Exception(f"unknown instruction:{op}")

        def parse_reg(self,reg_str):
                 return int(reg_str.strip().replace("x",""))

        def parse_mem_operand(self,operands):

            reg1=self.parse_reg(operands[0])
            offset_str, reg_str = operands[1].replace(")","").split("(")
            reg2=self.parse_reg(reg_str)
            offset=int(offset_str)
            return reg1,offset,reg2
            
        def fill_values(self, decoded, registers, labels):
         """Add actual register values into decoded dict"""
        if "rs1" in decoded:
           decoded["rs1_val"] = registers.read(decoded["rs1"])
        if "rs2" in decoded:
           decoded["rs2_val"] = registers.read(decoded["rs2"])
         # resolve label to line number
        if "label" in decoded:
              decoded["target_pc"] = labels[decoded["label"]]
        return decoded


                           