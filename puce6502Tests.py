#!/bin/env python3

"""
  Tests for puce6502, a MOS 6502 cpu emulator
  Last modified 21st of June 2023 - python version
  Copyright (c) 2023 Arthur Ferreira (arthur.ferreira2@gmail.com)

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions :

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
"""

"""
  6502 functonnal tests
  using Klaus Dormann's 6502 functonnal tests published at :
  https://github.com/Klaus2m5/6502_65C02_functional_tests

  The code down below was used during developpment for tests, optimization
  and troubleshooting. It is not required for normal operation

  It is provided so you can check the accuracy of the emultaion, modify it to
  to your will and test your changes
"""

import puce6502
import clock

# mnemonics
mn = [
    "BRK","ORA","UND","UND","UND","ORA","ASL","UND","PHP","ORA","ASL","UND","UND","ORA","ASL","UND",
    "BPL","ORA","UND","UND","UND","ORA","ASL","UND","CLC","ORA","UND","UND","UND","ORA","ASL","UND",
    "JSR","AND","UND","UND","BIT","AND","ROL","UND","PLP","AND","ROL","UND","BIT","AND","ROL","UND",
    "BMI","AND","UND","UND","UND","AND","ROL","UND","SEC","AND","UND","UND","UND","AND","ROL","UND",
    "RTI","EOR","UND","UND","UND","EOR","LSR","UND","PHA","EOR","LSR","UND","JMP","EOR","LSR","UND",
    "BVC","EOR","UND","UND","UND","EOR","LSR","UND","CLI","EOR","UND","UND","UND","EOR","LSR","UND",
    "RTS","ADC","UND","UND","UND","ADC","ROR","UND","PLA","ADC","ROR","UND","JMP","ADC","ROR","UND",
    "BVS","ADC","UND","UND","UND","ADC","ROR","UND","SEI","ADC","UND","UND","UND","ADC","ROR","UND",
    "UND","STA","UND","UND","STY","STA","STX","UND","DEY","UND","TXA","UND","STY","STA","STX","UND",
    "BCC","STA","UND","UND","STY","STA","STX","UND","TYA","STA","TXS","UND","UND","STA","UND","UND",
    "LDY","LDA","LDX","UND","LDY","LDA","LDX","UND","TAY","LDA","TAX","UND","LDY","LDA","LDX","UND",
    "BCS","LDA","UND","UND","LDY","LDA","LDX","UND","CLV","LDA","TSX","UND","LDY","LDA","LDX","UND",
    "CPY","CMP","UND","UND","CPY","CMP","DEC","UND","INY","CMP","DEX","UND","CPY","CMP","DEC","UND",
    "BNE","CMP","UND","UND","UND","CMP","DEC","UND","CLD","CMP","UND","UND","UND","CMP","DEC","UND",
    "CPX","SBC","UND","UND","CPX","SBC","INC","UND","INX","SBC","NOP","UND","CPX","SBC","INC","UND",
    "BEQ","SBC","UND","UND","UND","SBC","INC","UND","SED","SBC","UND","UND","UND","SBC","INC","UND"
]

# addressing modes for the match case below
am = [
    0, 10, 0, 0, 0, 3, 3, 0, 0, 2, 1, 0, 0, 7, 7, 0,
    6, 11, 0, 0, 0, 4, 4, 0, 0, 9, 0, 0, 0, 8, 8, 0,
    7, 10, 0, 0, 3, 3, 3, 0, 0, 2, 1, 0, 7, 7, 7, 0,
    6, 11, 0, 0, 0, 4, 4, 0, 0, 9, 0, 0, 0, 8, 8, 0,
    0, 10, 0, 0, 0, 3, 3, 0, 0, 2, 1, 0, 7, 7, 7, 0,
    6, 11, 0, 0, 0, 4, 4, 0, 0, 9, 0, 0, 0, 8, 8, 0,
    0, 10, 0, 0, 0, 3, 3, 0, 0, 2, 1, 0,12, 7, 7, 0,
    6, 11, 0, 0, 0, 4, 4, 0, 0, 9, 0, 0, 0, 8, 8, 0,
    0, 10, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 7, 7, 7, 0,
    6, 11, 0, 0, 4, 4, 5, 0, 0, 9, 0, 0, 0, 8, 0, 0,
    2, 10, 2, 0, 3, 3, 3, 0, 0, 2, 0, 0, 7, 7, 7, 0,
    6, 11, 0, 0, 4, 4, 5, 0, 0, 9, 0, 0, 8, 8, 9, 0,
    2, 10, 0, 0, 3, 3, 3, 0, 0, 2, 0, 0, 7, 7, 7, 0,
    6, 11, 0, 0, 0, 4, 4, 0, 0, 9, 0, 0, 0, 8, 8, 0,
    2, 10, 0, 0, 3, 3, 3, 0, 0, 2, 0, 0, 7, 7, 7, 0,
    6, 11, 0, 0, 0, 4, 4, 0, 0, 9, 0, 0, 0, 8, 8, 0
]


ram = bytearray(0x10000)

def readMem(address) :
    return ram[address]

def writeMem(address, value) :
    ram[address] = value



open('6502_functional_test.bin', 'rb').readinto(ram)

cpu = puce6502.Puce6502(readMem, writeMem)
cpu.rst();                                                                      # reset the CPU
cpu.PC = 0x400;                                                                 # set Program Counter to start of code

oldticks = clock.ticks
oldPC = cpu.PC
newPC = cpu.PC                                                                  # for detecting the BNE $FE when a test fails


# if you want to check the accuracy of the emulation, uncomment the while loop :

# while(True) :

#     b1 = ram[(newPC + 1) & 0xFFFF]
#     b2 = ram[(newPC + 2) & 0xFFFF]
#     op = ram[newPC]

#     print(f"{newPC:04X} {op:02X} ", end='')

#     match am[op] :
#         case  0x0 :                                                             # implied
#             print(f"       {mn[op]}          ", end='')
#         case  1 :                                                               # accumulator
#             print(f"       {mn[op]} A        ", end='')
#         case  2 :                                                               # immediate
#             print(f"{b1:02X}     {mn[op]} #${b1:02X}     ", end='')
#         case  3 :                                                               # zero page
#             print(f"{b1:02X}     {mn[op]} ${b1:02X}      ", end='')
#         case  4 :                                                               # zero page, X indexed
#             print(f"{b1:02X}     {mn[op]} ${b1:02X},X    ", end='')
#         case  5 :                                                               # zero page, Y indexed
#             print(f"{b1:02X}     {mn[op]} ${b1:02X},Y    ", end='')
#         case  6 :                                                               # relative
#             print(f"{b1:02X}     {mn[op]} ${b1:02X}      ", end='')
#         case  10 :                                                              # X indexed, indirect
#             print(f"{b1:02X}     {mn[op]} (${b1:02X},X)  ", end='')
#         case  11 :                                                              # indirect, Y indexed
#             print(f"{b1:02X}     {mn[op]} (${b1:02X}),Y  ", end='')
#         case  7 :                                                               # absolute
#             print(f"{b1:02X}{b2:02X}   {mn[op]} ${b2:02X}{b1:02X}    ", end='')
#         case  8 :                                                               # absolute, X indexed
#             print(f"{b1:02X}{b2:02X}   {mn[op]} ${b2:02X}{b1:02X},X  ", end='')
#         case  9 :                                                               # absolute, Y indexed
#             print(f"{b1:02X}{b2:02X}   {mn[op]} ${b2:02X}{b1:02X},Y  ", end='')
#         case  12 :                                                              # indirect
#             print(f"{b1:02X}{b2:02X}   {mn[op]} (${b2:02X}{b1:02X})  ", end='')

#     newPC = cpu.run(1)

#     print(f"A={cpu.A:02X}  X={cpu.X:02X}  Y={cpu.Y:02X}  S={cpu.SP:02X}  *S={ram[0x0100 + cpu.SP]:02X}  {'N' if cpu.S else '-'}{'V' if cpu.V else '-'}{'U' if cpu.U else '-'}{'B' if cpu.B else '-'}{'D' if cpu.D else '-'}{'I' if cpu.I else '-'}{'Z' if cpu.Z else '-'}{'C' if cpu.C else '-'}", end='')

#     print(f"   Cycles: {clock.ticks - oldticks}   Total: {clock.ticks}")
#     oldticks = clock.ticks

#     if newPC == 0x3469 :                                                        # 6502_functional_test SUCCESS
#         print(f"\nReached end of 6502_functional_test @ {newPC:04X} : SUCCESS !")
#         break

#     if newPC == oldPC :
#         print(f"\n\nLoop detected @ {newPC:04X} - dumping memory ...\n\n")
#         with open('memory.dump', 'wb') as f:
#             f.write(mem.ram)
#         exit()

#     oldPC = newPC



# Benchmarks
# comment the above while loop and uncomment the line below :

cpu.run(96240573)

# then, use the unix utility 'time' to evaluate the emulation speed



"""
    # test results :


    ## Using 6502_functional_test.bin :

    <--->
    3457 69 55     ADC #$55       A=AA  X=0E  Y=FF  S=FF  *S=34  NVUB----   Cycles: 2   Total: 96240555
    3459 C9 AA     CMP #$AA       A=AA  X=0E  Y=FF  S=FF  *S=34  -VUB--ZC   Cycles: 2   Total: 96240557
    345B D0 FE     BNE $FE        A=AA  X=0E  Y=FF  S=FF  *S=34  -VUB--ZC   Cycles: 2   Total: 96240559
    345D AD 0002   LDA $0200      A=2B  X=0E  Y=FF  S=FF  *S=34  -VUB---C   Cycles: 4   Total: 96240563
    3460 C9 2B     CMP #$2B       A=2B  X=0E  Y=FF  S=FF  *S=34  -VUB--ZC   Cycles: 2   Total: 96240565
    3462 D0 FE     BNE $FE        A=2B  X=0E  Y=FF  S=FF  *S=34  -VUB--ZC   Cycles: 2   Total: 96240567
    3464 A9 F0     LDA #$F0       A=F0  X=0E  Y=FF  S=FF  *S=34  NVUB---C   Cycles: 2   Total: 96240569
    3466 8D 0002   STA $0200      A=F0  X=0E  Y=FF  S=FF  *S=34  NVUB---C   Cycles: 4   Total: 96240573

    Reached end of 6502_functional_test @ 3469 : SUCCESS !


    This means puce6502 passes the 6502 functionnal tests :

                            ; S U C C E S S ************************************************
                            ; -------------
                                    success         ;if you get here everything went well
    3469 : 4c6934          >        jmp *           ;test passed, no errors

                            ; -------------
                            ; S U C C E S S ************************************************


    ## "Benchmarks", using a core i5-8365u laptop

    $ time python ./puce6502Tests.py

    match case version :
    real    0m43.328s
    user    0m0.015s
    sys     0m0.000s


    if elif version :
    real    0m39.126s
    user    0m0.000s
    sys     0m0.015s


    if elif with binary search tree deep 4 :
    real    0m23.438s
    user    0m0.000s
    sys     0m0.015s


    if elif with binary search tree deep 5 :
    real    0m22.976s
    user    0m0.015s
    sys     0m0.000s

    kudos to 'phire' : https://www.reddit.com/r/EmuDev/comments/16f021n/comment/k02qnl8/?utm_source=share&utm_medium=web2x&context=3
"""