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

### Date: 10-Apr-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~2 hours  

Final push today. We finally merged Maneesh’s hardware-accurate cache model into the main pipeline. It wasn't as smooth as we hoped—we found a handful of bugs during the merge, mostly weird edge cases in the forwarding unit and some stall logic that got trippy with the new cache latencies. We ended up building a full test suite in `tests/` just to be 100% sure the core logic is solid. Spent the rest of the time cleaning up the repo and squashing all those messy merge commits so it looks decent on GitHub. Everything's finally working across all modes. 

---

### Date: 09-Apr-2026
**Members:** Maneesh  
**Duration:** ~20 minutes  

Maneesh finished the heavy lifting on the cache side today. He got the L1 (I and D) and L2 levels up and running with the full Write-Back logic we talked about. All the data-access paths are now talking to the memory object correctly. He hit his deadline, so we're good to go for the final integration.

---

### Date: 03-Apr-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~20 minutes  

Quick design session for the cache. We decided to go with LRU and Random as our replacement policies—should be interesting to see which one performs better. After we talked through some memory stage changes I’d already started, I handed over the integration and data-access enablement to Maneesh. He's taking the lead on the multi-level hierarchy now while I keep an eye on the pipeline stability.

---

### Date: 02-Apr-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~40 minutes  

Starting Phase 2. While we were looking at the cache requirements, we actually spotted some subtle bugs in our Phase 1 pipeline, mostly around how we were prioritizing forwarding. Instead of just patching them, we decided to overhaul the logic as part of the Phase 2 transition to keep things clean. Sketched out a rough plan for the L1/L2 split.

---

### Date: 08-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~1.5 hours

Spent most of the session running the simulator on bubble sort and debugging. The output was completely wrong when pipelining and forwarding were both on — turned out there were two bugs hiding in `forwarding.py`. One was that we were forwarding the memory address instead of the actual loaded value for LW instructions. The other was that EX and MEM forwarding priority was flipped, so an older value from a previous loop iteration was winning over the fresh one. Took a while to trace but fixed both. Tested all modes after — all give `[1, 2, 3, 5, 8]` now. Also ran a few simple hand-written programs to make sure nothing else was broken. Cleaned up the repo before wrapping up — got rid of pycache files that somehow got committed, fixed some `__init__` files that were missing the dot, added a `.gitignore` so it doesn't happen again.

---

### Date: 07-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~20 minutes

Went through the hazard detection and pipeline code together. Stall counts looked off at first — figured out that the latency values from `config.json` weren't being used properly. Fixed that. Also checked that the no-forwarding path was already logging hazards (it wasn't before — added that). Everything seemed to be working fine after these fixes.

---

### Date: 03-Mar-2026
**Members:** Vinay Sai, Maneesh  
**Duration:** ~15 minutes

Maneesh took over the simulator side forwarding unit, and the main pipeline loop. Vinay did the stages part but Maneesh did most of the heavy lifting on this part. Talked about how to handle branches in the pipeline (flushing IF_ID and ID_EX on a taken BNE/JAL) and agreed on using simple Python variables for the pipeline registers (IF_ID, ID_EX, EX_MEM, MEM_WB).

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
