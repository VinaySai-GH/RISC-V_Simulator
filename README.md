# RISC-V Simulator

A RISC-V pipeline simulator inspired by Ripes, built as part of the Computer Organization & Architecture course (2026).

## Features

- **Supported instructions:** ADD, SUB, ADDI, SLT, LW, SW, BNE, JAL, AND, OR
- **5-stage pipeline:** Fetch → Decode → Execute → Memory → Writeback
- **Data forwarding** (enable/disable via flag or config)
- **Hazard detection:** RAW data hazards, load-use hazards, control hazards
- **Variable instruction latencies** via `config.json`
- **Output:** stall count, IPC, final register state, sorted array
- **Bubble sort** supported and tested

## Usage

```bash
python main.py program.asm                   # uses config.json defaults
python main.py program.asm --forwarding      # enable forwarding
python main.py program.asm --no-forwarding   # disable forwarding
python main.py program.asm --no-pipeline     # simple non-pipelined mode
```

## Config File (`config.json`)

```json
{
  "pipeline": true,
  "forwarding": true,
  "latencies": {
    "ADD":  1,
    "SUB":  1,
    "LW":   2,
    "SW":   1,
    "BNE":  1,
    "JAL":  1,
    "ADDI": 1,
    "SLT":  1
  }
}
```

## Assembly Syntax

```asm
LABEL:  add  x1, x2, x3      # rd, rs1, rs2
        sub  x1, x2, x3
        addi x1, x2, 10      # rd, rs1, immediate
        lw   x1, 0(x2)       # rd, offset(base)
        sw   x1, 0(x2)       # rs2, offset(base)
        bne  x1, x2, LABEL   # rs1, rs2, label
        jal  x0, LABEL       # rd, label
```

Comments start with `#`. Labels end with `:`.

---

## Minutes of Meeting

---

### Date: 08-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~1.5 hours  
**Discussion:**
Tested the full simulator on the bubble sort program. Discovered a bug in the pipelined + forwarding path — the sorted output was wrong (`[2, 1, 8, 3, 5]` instead of `[1, 2, 3, 5, 8]`). Traced it to two issues in `forwarding.py`: (1) `try_forward` was using `alu_result` for LW instructions instead of `mem_data`, forwarding the address instead of the loaded value; (2) EX-EX and MEM-EX forwarding priority was reversed, so a stale register value from a previous loop iteration could override a fresh reset. Both were fixed and the simulator was verified to work correctly across all modes (pipeline+fwd, pipeline no-fwd, no-pipeline). Also manually tested with simple programs. Cleaned up the repo — removed tracked `__pycache__` files, fixed misnamed `__init__py` files, and added `.gitignore`.

---

### Date: 07-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~20 minutes  
**Discussion:**
Reviewed hazard detection logic and overall simulator flow. Checked that stall counting was working correctly. Resolved issues with instruction latency not being correctly applied from `config.json`. Verified that the no-forwarding path correctly inserts stalls for RAW hazards and control hazards. Discussed the `run_pipelined_no_forwarding` approach and confirmed the hazard log was being populated in that path.

---

### Date: 03-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~15 minutes  
**Discussion:**
Maneesh took on the remaining simulator work — pipeline stages, forwarding unit, and the pipeline controller. Vinay assisted where needed. Discussed how to structure the 5-stage pipeline loop and how branch resolution (BNE, JAL) should interact with pipeline flushing. Agreed to use a single-pass loop where each stage is modelled as a Python variable (IF_ID, ID_EX, EX_MEM, MEM_WB).

---

### Date: 02-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~15 minutes  
**Discussion:**
Vinay completed the assembler (`utils/assembler.py`) and instruction decoder (`core/decoder.py`). The assembler handles label resolution, comment stripping, and multi-format operand parsing. The decoder supports R, I, S, B, and J type instructions. Discussed what still remained — pipeline stages, ALU, register file, memory, forwarding — and divided remaining work for the next session.

---

### Date: 24-Feb-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~10 minutes  
**Discussion:**
Kickoff meeting. Decided on the overall file and class structure for the simulator. Created the folder layout: `core/` (ALU, decoder, memory, registers), `simulator/` (pipeline, stages, forwarding), `utils/` (assembler, config loader). Agreed to use a JSON config file for pipeline/forwarding flags and instruction latencies. Decided on Python as the implementation language.

---
