from core.decoder import Decoder
from core.alu import ALU

decoder = Decoder()
alu     = ALU()

def fetch(instructions, pc, cache_controller=None, cycle=0):
    if pc < 0 or pc >= len(instructions):
        return None, 0

    if cache_controller is None:
        return instructions[pc], 1

    instruction_address = pc * 4
    latency = cache_controller.fetch_instruction(instruction_address, cycle)
    return instructions[pc], latency

def decode(instruction):
    if instruction is None:
        return None
    return decoder.decode(instruction)

def execute(decoded, registers=None):
    if decoded is None:
        return None

    # if registers provided, re-read fresh values (no-forwarding mode)
    if registers is not None:
        if "rs1" in decoded:
            decoded["rs1_val"] = registers.read(decoded["rs1"])
        if "rs2" in decoded:
            decoded["rs2_val"] = registers.read(decoded["rs2"])

    op = decoded["op"]

    if decoded["type"] == "R":
        a = decoded["rs1_val"]
        b = decoded["rs2_val"]
    elif decoded["type"] == "I":
        a = decoded["rs1_val"]
        b = decoded["offset"]
    elif decoded["type"] == "S":
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

def memory_access(decoded, memory, cache_controller=None, cycle=0):
    if decoded is None:
        return None, 0

    latency = 1

    if decoded["op"] == "LW":
        if cache_controller is not None:
            decoded["mem_data"], latency = cache_controller.load_word(
                decoded["alu_result"], cycle
            )
        else:
            decoded["mem_data"] = memory.load(decoded["alu_result"])
    elif decoded["op"] == "SW":
        if cache_controller is not None:
            latency = cache_controller.store_word(
                decoded["alu_result"], decoded["rs2_val"], cycle
            )
        else:
            memory.store(decoded["alu_result"], decoded["rs2_val"])
    return decoded, latency

def writeback(decoded, registers):
    if decoded is None:
        return
    op = decoded["op"]
    if op in ("ADD", "SUB", "ADDI", "AND", "OR", "SLT"):
        registers.write(decoded["rd"], decoded["alu_result"])
    elif op == "LW":
        registers.write(decoded["rd"], decoded["mem_data"])
    elif op == "JAL":
        if decoded["rd"] != 0:
            registers.write(decoded["rd"], decoded.get("pc_plus_4", 0))
