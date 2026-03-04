from core.decoder import Decoder
from core.alu import ALU

decoder = Decoder()
alu = ALU()

def fetch(instructions, pc):
    """Get instruction at current PC"""
    if pc >= len(instructions):
        return None          # no more instructions
    return instructions[pc]

def decode(instruction):
    """Break instruction into parts"""
    if instruction is None:
        return None
    return decoder.decode(instruction)

def execute(decoded):
    """Run the ALU"""
    if decoded is None:
        return None

    op  = decoded["op"]

    # R-type: ADD, SUB, AND, OR, SLT
    if decoded["type"] == "R":
        a = decoded["rs1_val"]
        b = decoded["rs2_val"]

    # I-type: LW
    elif decoded["type"] == "I":
        a = decoded["rs1_val"]
        b = decoded["offset"]

    # S-type: SW
    elif decoded["type"] == "S":
        a = decoded["rs1_val"]
        b = decoded["offset"]

    # B-type: BNE
    elif decoded["type"] == "B":
        a = decoded["rs1_val"]
        b = decoded["rs2_val"]

    # J-type: JAL
    elif decoded["type"] == "J":
        a, b = 0, 0

    result = alu.execute(op, a, b)
    decoded["alu_result"] = result
    return decoded

def memory_access(decoded, memory):
    """Load or store from RAM"""
    if decoded is None:
        return None

    if decoded["op"] == "LW":
        address = decoded["alu_result"]
        decoded["mem_data"] = memory.load(address)

    elif decoded["op"] == "SW":
        address = decoded["alu_result"]
        memory.store(address, decoded["rs2_val"])

    return decoded

def writeback(decoded, registers):
    """Write result back to register"""
    if decoded is None:
        return

    op = decoded["op"]

    if op in ("ADD", "SUB", "AND", "OR", "SLT"):
        registers.write(decoded["rd"], decoded["alu_result"])

    elif op == "LW":
        registers.write(decoded["rd"], decoded["mem_data"])

    # SW, BNE, JAL don't write to a register