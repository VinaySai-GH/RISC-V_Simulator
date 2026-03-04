class ALU:
    def execute(self, op, a, b):
        if op == "ADD":
            return a + b

        elif op == "SUB":
            return a - b

        elif op == "AND":
            return a & b

        elif op == "OR":
            return a | b

        elif op == "SLT":
            # Set Less Than — returns 1 if a < b, else 0
            return 1 if a < b else 0

        elif op == "LW":
            # address = base + offset
            return a + b

        elif op == "SW":
            # address = base + offset
            return a + b

        elif op == "BNE":
            # not equal? return 1 (take branch), else 0
            return 1 if a != b else 0

        elif op == "JAL":
            # unconditional jump — always taken
            return 1

        else:
            raise Exception(f"ALU: unknown operation '{op}'")




 #alu.execute("ADD", 5, 3)  → 8
 #alu.execute("SLT", 2, 5)  → 1   (2 < 5, so yes)
#alu.execute("BNE", 3, 3)  → 0   (3 == 3, so don't branch)
#alu.execute("BNE", 3, 4)  → 1   (3 != 4, so branch!) 