class ALU:
    def execute(self, op, a, b):
        if op == "ADD":
            return a + b
        elif op == "SUB":
            return a - b
        elif op == "ADDI":
            return a + b
        elif op == "AND":
            return a & b
        elif op == "OR":
            return a | b
        elif op == "SLT":
            return 1 if a < b else 0
        elif op == "MUL":
            return a * b
        elif op == "LW":
            return a + b
        elif op == "SW":
            return a + b
        elif op == "BNE":
            return 1 if a != b else 0
        elif op == "JAL":
            return 1
        else:
            raise Exception(f"ALU: unknown op '{op}'")