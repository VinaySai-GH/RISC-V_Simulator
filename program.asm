INIT:   addi x10, x0, 4
        addi x12, x0, 0

OUTER:  addi x11, x0, 0
        addi x12, x0, 0

INNER:  lw   x13, 0(x12)
        lw   x14, 4(x12)
        slt  x15, x13, x14
        bne  x15, x0, NOSWAP
        sw   x14, 0(x12)
        sw   x13, 4(x12)

NOSWAP: addi x12, x12, 4
        addi x11, x11, 1
        sub  x16, x10, x11
        bne  x16, x0, INNER
        addi x10, x10, -1
        bne  x10, x0, OUTER

DONE:   jal  x0, DONE