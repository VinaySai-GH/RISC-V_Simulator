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

Spent most of the session running the simulator on bubble sort and debugging. The output was completely wrong when pipelining and forwarding were both on — turned out there were two bugs hiding in `forwarding.py`. One was that we were forwarding the memory address instead of the actual loaded value for LW instructions. The other was that EX and MEM forwarding priority was flipped, so an older value from a previous loop iteration was winning over the fresh one. Took a while to trace but fixed both. Tested all modes after — all give `[1, 2, 3, 5, 8]` now. Also ran a few simple hand-written programs to make sure nothing else was broken. Cleaned up the repo before wrapping up — got rid of pycache files that somehow got committed, fixed some `__init__` files that were missing the dot, added a `.gitignore` so it doesn't happen again.

---

### Date: 07-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~20 minutes

Went through the hazard detection and pipeline code together. Stall counts looked off at first — figured out that the latency values from `config.json` weren't being used properly. Fixed that. Also checked that the no-forwarding path was actually logging hazards (it wasn't before — added that). Everything seemed to be working fine after these fixes.

---

### Date: 03-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~15 minutes

Maneesh took over the simulator side — pipeline stages, forwarding unit, and the main pipeline loop. Vinay helped out here and there but Maneesh did most of the heavy lifting on this part. Talked about how to handle branches in the pipeline (flushing IF_ID and ID_EX on a taken BNE/JAL) and agreed on using simple Python variables for the pipeline registers (IF_ID, ID_EX, EX_MEM, MEM_WB).

---

### Date: 02-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~15 minutes

Vinay finished the assembler and decoder. The assembler strips comments, resolves labels, and parses all the operand formats. The decoder breaks each instruction into its fields depending on type (R, I, S, B, J). Discussed what was left to do — ALU, register file, memory, full pipeline — and figured out who'd do what next.

---

### Date: 24-Feb-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~10 minutes

First meeting. Decided on the basic structure — split things into `core/`, `simulator/`, and `utils/` folders. Agreed to use a JSON config file so latencies and flags like forwarding/pipeline aren't hardcoded. Picked Python since it's easier to prototype in. Nothing was built yet, just planning.

---
