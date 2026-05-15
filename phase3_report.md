# Phase 3 Report: Virtual Memory and Trace Replay

## Design Summary

This phase extends the simulator with a trace replay mode for virtual-memory experiments. Trace replay reads each trace instruction in order and charges timing for arithmetic operations, address translation, and data-cache access.

The virtual memory system uses:

- One process with a flat page table.
- 32-bit virtual addresses.
- 4 KB pages in the reporting configuration.
- A data TLB.
- Page-table walks on TLB misses.
- Page faults on first access to unmapped pages.
- Finite physical memory represented as frames.
- LRU page replacement when physical memory is full.
- Dirty-bit tracking for store accesses and dirty eviction/writeback statistics.

The trace replay path does not simulate instruction-cache misses, as required. Load and store addresses are treated as virtual addresses, translated through the DTLB/page table, and then used for a PIPT L1 data-cache access.
The trace-mode register file is updated for `L`, `S`, `ADD`, and `MUL` operands from the trace.

## Changes Made

- Added trace replay mode through `--trace`.
- Added a virtual memory subsystem with DTLB, page table, page faults, frame allocation, replacement, and dirty eviction tracking.
- Added config-driven memory and VM parameters.
- Added `ADD` and `MUL` timing support for traces.
- Added trace-mode register handling for load destinations, store sources, and arithmetic operands.
- Added support for running with no L2 cache by setting `l2_size_bytes = 0`.
- Updated `example.ini` to match the uniform reporting configuration.

## Trace Format

The simulator accepts the provided Phase 3 trace format:

```text
L 0x1000 x5
S 0x1004 x6
ADD x7 x5 x6
MUL x8 x7 x9
```

For `L` and `S`, the address is interpreted as a virtual address. `ADD` has latency 1 cycle and `MUL` has latency 3 cycles.

## Reporting Configuration

The results below use `example.ini` with:

- Replacement policy: `lru`
- Page size: 4 KB
- DTLB entries: 16
- Physical frames: 64
- TLB hit latency: 1
- Page-walk latency: 10
- Page-fault latency: 50
- L1 access latency: 1
- L1 data cache: 4 KB direct mapped
- L2 cache: disabled
- Cache type: PIPT, with TLB access before cache access

## Results

| Trace | Total cycles | Instructions | IPC | Stalls | TLB hits | TLB misses | Page walks | Page faults | Page evictions | Dirty evictions | Translation penalty |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trace01 | 37218120 | 715724 | 0.0192 | 36502396 | 357854 | 8 | 8 | 8 | 0 | 0 | 358334 |
| trace02 | 37217552 | 715704 | 0.0192 | 36501848 | 357836 | 16 | 16 | 16 | 0 | 0 | 358796 |
| trace03 | 40440838 | 715752 | 0.0177 | 39725086 | 0 | 357876 | 357876 | 17 | 0 | 0 | 3579610 |
| trace04 | 37705888 | 715728 | 0.0190 | 36990160 | 178516 | 179348 | 179348 | 32 | 0 | 0 | 1973596 |
| trace05 | 40316568 | 715732 | 0.0178 | 39600836 | 13010 | 344856 | 344856 | 64 | 0 | 0 | 3464770 |
| trace06 | 22551832 | 715728 | 0.0317 | 21836104 | 0 | 357864 | 357864 | 357864 | 357800 | 107798 | 21471840 |
| trace07 | 40880564 | 715736 | 0.0175 | 40164828 | 208880 | 148988 | 148988 | 59900 | 59836 | 57100 | 4693760 |
| trace08 | 22552210 | 715740 | 0.0317 | 21836470 | 0 | 357870 | 357870 | 357870 | 357806 | 71269 | 21472200 |
| trace09 | 58333788 | 715752 | 0.0123 | 57618036 | 0 | 357876 | 357876 | 357876 | 357812 | 125515 | 21472560 |
| trace10 | 36195981 | 715712 | 0.0198 | 35480269 | 285083 | 72773 | 72773 | 1716 | 1652 | 1652 | 1098613 |

## Observations

Traces with strong locality, such as `trace01` and `trace02`, have very few page faults after the initial working set is mapped. Traces such as `trace06`, `trace08`, and `trace09` show heavy page fault and eviction behavior, meaning their access patterns exceed the 64-frame physical memory configuration or repeatedly cycle through pages in a way that defeats locality.
