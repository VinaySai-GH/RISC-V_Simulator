from core.decoder import Decoder
from core.alu import ALU

decoder = Decoder()
alu     = ALU()

def fetch(instructions, pc):
    if pc >= len(instructions):
        return None
    return instructions[pc]

def decode(instruction):
    if instruction is None:
        return None
    return decoder.decode(instruction)

def execute(decoded):
    if decoded is None:
        return None

    op = decoded["op"]

    if decoded["type"] == "R":
        a = decoded["rs1_val"]
        b = decoded["rs2_val"]

    elif decoded["type"] == "I":
        a = decoded["rs1_val"]
        b = decoded["offset"]

    elif decoded["type"] == "S":
        # address = base(rs1) + offset
        a = decoded["rs1_val"]
        b = decoded["offset"]

    elif decoded["type"] == "B":
        a = decoded["rs1_val"]
        b = decoded["rs2_val"]

    elif decoded["type"] == "J":
        a, b = 0, 0

    result = alu.execute(op, a, b)
    decoded["alu_result"] = result
    return decoded

def memory_access(decoded, memory):
    if decoded is None:
        return None
    if decoded["op"] == "LW":
        decoded["mem_data"] = memory.load(decoded["alu_result"])
    elif decoded["op"] == "SW":
        address = decoded["alu_result"]
        value   = decoded["rs2_val"]
        memory.store(address, value)
    return decoded

def writeback(decoded, registers):
    if decoded is None:
        return
    op = decoded["op"]
    if op in ("ADD", "SUB", "ADDI", "AND", "OR", "SLT"):
        registers.write(decoded["rd"], decoded["alu_result"])
    elif op == "LW":
        registers.write(decoded["rd"], decoded["mem_data"])