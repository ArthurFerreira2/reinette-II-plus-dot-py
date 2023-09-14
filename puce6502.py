"""
    puce6502, a MOS 6502 cpu emulator
    Last modified 21st of August 2023 - python version
    Copyright (c) 2023 Arthur Ferreira

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

import clock                                                                    # global variable ticks

class Puce6502() :

    def __init__(self, readMem, writeMem):

        self.readMem = readMem
        self.writeMem = writeMem

        # CONSTANTS
        self.CARRY = 0x01
        self.ZERO  = 0x02
        self.INTR  = 0x04
        self.DECIM = 0x08
        self.BREAK = 0x10
        self.UNDEF = 0x20
        self.OFLOW = 0x40
        self.SIGN  = 0x80

        self.C = 0                                                              # CARRY
        self.Z = 0                                                              # ZERO
        self.I = 0                                                              # INTR
        self.D = 0                                                              # DECIM
        self.B = 0                                                              # BREAK
        self.U = 0                                                              # UNDEF
        self.V = 0                                                              # OFLOW
        self.S = 0                                                              # SIGN

        self.A  = 0                                                             # Accumulator,
        self.X  = 0                                                             # X index
        self.Y  = 0                                                             # Y index
        self.PC = 0                                                             # Program Counter
        self.SP = 0                                                             # Stack Pointer

        self.rst()                                                              # perform a reset


    def setPC(self, address) :
        self.PC = address


    def getPC(self) :
        return self.PC


    def getP(self):
        return self.C*self.CARRY + self.Z*self.ZERO + self.I*self.INTR + self.D*self.DECIM + self.B*self.BREAK + self.U*self.UNDEF + self.V*self.OFLOW + self.S*self.SIGN


    def setP(self, value):
        self.C = 1 if value & self.CARRY else 0
        self.Z = 1 if value & self.ZERO  else 0
        self.I = 1 if value & self.INTR  else 0
        self.D = 1 if value & self.DECIM else 0
        self.B = 1 if value & self.BREAK else 0
        self.U = 1 if value & self.UNDEF else 0
        self.V = 1 if value & self.OFLOW else 0
        self.S = 1 if value & self.SIGN  else 0


    def rst(self) :                                                             # Reset
        self.PC = self.readMem(0xFFFC) | (self.readMem(0xFFFD) << 8)
        self.SP = 0xFD
        self.I = 1
        self.U = 1
        clock.ticks += 7


    def irq(self) :                                                             # Interupt Request
        if not self.I :
            return
        self.PC = (self.PC + 1) & 0xFFFF
        self.writeMem(0x100 + self.SP, (self.PC >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        self.writeMem(0x100 + self.SP, self.PC & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        self.writeMem(0x100 + self.SP, self.getP() & ~self.BREAK)
        self.SP = (self.SP - 1) & 0xFF
        self.PC = self.readMem(0xFFFE) | (self.readMem(0xFFFF) << 8)
        clock.ticks += 7


    def nmi(self) :                                                             # Non Maskable Interupt
        self.I = 1
        self.PC = (self.PC + 1) & 0xFFFF
        self.writeMem(0x100 + self.SP, (self.PC >> 8) & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        self.writeMem(0x100 + self.SP, self.PC & 0xFF)
        self.SP = (self.SP - 1) & 0xFF
        self.writeMem(0x100 + self.SP, self.getP() & ~self.BREAK)
        self.SP = (self.SP - 1) & 0xFF
        self.PC = self.readMem(0xFFFA) | (self.readMem(0xFFFB) << 8)
        clock.ticks += 7


    """  Addressing modes abbreviations used in the comments down below :

    IMP : Implied or Implicit              : DEX, RTS, CLC : 25 instructions
    ACC : Accumulator                      : ASL, ROR, DEC :  4 instructions
    IMM : Immediate                        : LDA #$A5      : 11 instructions
    ZPG : Zero Page                        : LDA $81       : 21 instructions
    ZPX : Zero Page Indexed with X         : LDA $55,X     : 16 instructions
    ZPY : Zero Page Indexed with Y         : LDX $55,Y     :  2 instructions
    REL : Relative                         : BEQ LABEL12   :  8 instructions
    ABS : Absolute                         : LDA $2000     : 23 instructions
    ABX : Absolute Indexed with X          : LDA $2000,X   : 15 instructions
    ABY : Absolute Indexed with Y          : LDA $2000,Y   :  9 instructions
    IND : Indirect                         : JMP ($1020)   :  1 instructions
    IZX : ZP (Pre)Indexed Indirect with X  : LDA ($55,X)   :  8 instructions
    IZY : ZP Indirect (Post)Indexed with Y : LDA ($55),Y   :  8 instructions

    The variables value8, value16 and address are used to temporarely
    hold 8bits, 16bits data and memory addresses (which are also 16bits wide)


    Optimizations :
    https://www.reddit.com/r/EmuDev/comments/16f021n/comment/k02qnl8/?utm_source=share&utm_medium=web2x&context=3

    using a 'binary search tree' to speed up instruction lookup

    00  10  20  30  40  50  60  70  80  90  A0  B0  C0  D0  E0  FF
                                  1
                  2                               2
          3               3               3               3
      4       4       4       4       4       4       4       4
    5   5   5   5   5   5   5   5   5   5   5   5   5   5   5   5

    Thank you 'phire' for the idea :-)

    """

    def run(self, cycleCount) :

        cycleCount += clock.ticks                                               # cycleCount becomes the target ticks value
        while (clock.ticks < cycleCount) :

            inst = self.readMem(self.PC)                                        # fetch instruction
            self.PC = (self.PC + 1) & 0xFFFF                                    # increment Program Counter

            if inst < 0x80 :
                if inst < 0x40 :
                    if inst < 0x20 :
                        if inst < 0x10 :
                            if inst < 0x08 :
                            # 0x00 to 0x07

                                if inst ==  0x00 :                              # IMP BRK
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.writeMem(0x100 + self.SP, ((self.PC) >> 8) & 0xFF)
                                    self.SP = (self.SP - 1) & 0xFF
                                    self.writeMem(0x100 + self.SP, self.PC & 0xFF)
                                    self.SP = (self.SP - 1) & 0xFF
                                    self.writeMem(0x100 + self.SP, self.getP() | self.BREAK)
                                    self.SP = (self.SP - 1) & 0xFF
                                    self.I = 1
                                    self.D = 0
                                    self.PC = self.readMem(0xFFFE) | (self.readMem(0xFFFF) << 8)
                                    clock.ticks += 7
                                    continue

                                elif inst ==  0x01 :                            # IZX ORA
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    self.A |= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x05 :                            # ZPG ORA
                                    self.A |= self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x06 :                            # ZPG ASL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = self.readMem(address) << 1
                                    self.C = value16 > 0xFF
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 5
                                    continue

                            else :
                            # 0x08 to 0x0F

                                if inst ==  0x08 :                              # IMP PHP
                                    self.writeMem(0x100 + self.SP, self.getP() | self.BREAK)
                                    self.SP = (self.SP - 1) & 0xFF
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x09 :                            # IMM ORA
                                    self.A |= self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x0A :                            # ACC ASL
                                    value16 = self.A << 1
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x0D :                            # ABS ORA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A |= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x0E :                            # ABS ASL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = self.readMem(address) << 1
                                    self.C = value16 > 0xFF
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 6
                                    continue

                        else :
                            if inst < 0x18 :
                            # 0x10 to 0x17

                                if inst ==  0x10 :                              # REL BPL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if not self.S :                             # jump taken
                                        clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x11 :                            # IZY ORA
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    if ((address & 0xFF) + self.Y) & 0xFF00 :
                                        clock.ticks += 6
                                    else :
                                        clock.ticks += 5
                                    address = (address + self.Y) & 0xFFFF
                                    self.A |= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x15 :                            # ZPX ORA
                                    self.A |= self.readMem((self.readMem(self.PC) + self.X) & 0xFF)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x16 :                            # ZPX ASL
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = self.readMem(address) << 1
                                    self.writeMem(address, value16 & 0xFF)
                                    self.C = value16 > 0xFF
                                    self.Z = value16 == 0
                                    self.S = (value16 & 0xFF) > 0x7F
                                    clock.ticks += 6
                                    continue

                            else :
                            # 0x18 to 0x1F

                                if inst ==  0x18 :                              # IMP CLC
                                    self.C = 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x19 :                            # ABY ORA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 5
                                    else:
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    self.A |= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x1D :                            # ABX ORA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    self.A |= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x1E :                            # ABX ASL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value16 = self.readMem(address) << 1
                                    self.C = value16 > 0xFF
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 7
                                    continue

                    else :
                        if inst < 0x30 :
                            if inst < 0x28 :
                            # 0x20 to 0x27

                                if inst ==  0x20 :                              # ABS JSR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.writeMem(0x100 + self.SP, (self.PC >> 8) & 0xFF)
                                    self.SP = (self.SP - 1) & 0xFF
                                    self.writeMem(0x100 + self.SP, self.PC & 0xFF)
                                    self.SP = (self.SP - 1) & 0xFF
                                    self.PC = address
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x21 :                            # IZX AND
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    self.A &= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x24 :                            # ZPG BIT
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = (self.A & value8) == 0
                                    self.setP((self.getP() & 0x3F) | (value8 & 0xC0))
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x25 :                            # ZPG AND
                                    self.A &= self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x26 :                            # ZPG ROL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = (self.readMem(address) << 1) | self.C
                                    self.C = (value16 & 0x100) != 0
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 5
                                    continue

                            else :
                            # 0x28 to 0x2F

                                if inst ==  0x28 :                              # IMP PLP
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.setP(self.readMem(0x100 + self.SP) | self.UNDEF)
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x29 :                            # IMM AND
                                    self.A &= self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x2A :                            # ACC ROL
                                    value16 = (self.A << 1) | self.C
                                    self.C = (value16 & 0x100) != 0
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x2C :                            # ABS BIT
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = (self.A & value8) == 0
                                    self.setP((self.getP() & 0x3F) | (value8 & 0xC0))
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x2D :                            # ABS AND
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A &= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x2E :                            # ABS ROL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = (self.readMem(address) << 1) | self.C
                                    self.C = (value16 & 0x100) != 0
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 6
                                    continue


                        else :
                            if inst < 0x38 :
                            # 0x30 to 0x37

                                if inst ==  0x30 :                              # REL BMI
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if self.S :
                                        clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x31 :                            # IZY AND
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    if ((address & 0xFF) + self.Y) & 0xFF00 :
                                        clock.ticks += 6
                                    else :
                                        clock.ticks += 5
                                    address = (address + self.Y) & 0xFFFF
                                    self.A &= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x35 :                            # ZPX AND
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A &= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x36 :                            # ZPX ROL
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = (self.readMem(address) << 1) | self.C
                                    self.C = value16 > 0xFF
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 6
                                    continue

                            else :
                            # 0x38 to 0x3F

                                if inst ==  0x38 :                              # IMP SEC
                                    self.C = 1
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x39 :                            # ABY AND
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    self.A &= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x3D :                            # ABX AND
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    self.A &= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x3E :                            # ABX ROL
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value16 = (self.readMem(address) << 1) | self.C
                                    self.C = value16 > 0xFF
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 7
                                    continue

                else :
                    if inst < 0x60 :
                        if inst < 0x50 :
                            if inst < 0x48 :
                            # 0x40 to  0x47

                                if inst ==  0x40 :                              # IMP RTI
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.setP(self.readMem(0x100 + self.SP))
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.PC = self.readMem(0x100 + self.SP)
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.PC |= self.readMem(0x100 + self.SP) << 8
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x41 :                            # IZX EOR
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    self.A ^= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x45 :                            # ZPG EOR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A ^= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x46 :                            # ZPG LSR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.C = (value8 & 1) != 0
                                    value8 = value8 >> 1
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 5
                                    continue
                            else :
                                # 0x48 to 0x4F

                                if inst ==  0x48 :                              # IMP PHA
                                    self.writeMem(0x100 + self.SP, self.A)
                                    self.SP = (self.SP - 1) & 0xFF
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x49 :                            # IMM EOR
                                    self.A ^= self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x4A :                            # ACC LSR
                                    self.C = (self.A & 1) != 0
                                    self.A = self.A >> 1
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x4C :                            # ABS JMP
                                    self.PC = self.readMem(self.PC) | (self.readMem(self.PC + 1) << 8)
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x4D :                            # ABS EOR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A ^= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x4E :                            # ABS LSR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.C = (value8 & 1) != 0
                                    value8 = value8 >> 1
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 6
                                    continue

                        else :
                            if inst < 0x58 :
                            # 0x50 to 0x5F

                                if inst ==  0x50 :                              # REL BVC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if not self.V :
                                        clock.ticks += 1
                                        if address & self.SIGN:
                                            address |= 0xFF00
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x51 :                            # IZY EOR
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    if ((address & 0xFF) + self.Y) & 0xFF00 :
                                        clock.ticks += 6
                                    else :
                                        clock.ticks += 5
                                    self.A ^= self.readMem((address + self.Y) & 0xFFFF)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x55 :                            # ZPX EOR
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A ^= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x56 :                            # ZPX LSR
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.C = (value8 & 1) != 0
                                    value8 = value8 >> 1
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x58 :                            # IMP CLI
                                    self.I = 0
                                    clock.ticks += 2
                                    continue

                            else :
                                # 0x58 to 0x5F

                                if inst ==  0x59 :                              # ABY EOR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    self.A ^= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x5D :                            # ABX EOR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    self.A ^= self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0x5E :                            # ABX LSR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.C = (value8 & 1) != 0
                                    value8 = value8 >> 1
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 7
                                    continue

                    else :
                        if inst < 0x70 :
                            if inst < 0x68 :
                            # 0x60 to 0x67

                                if inst ==  0x60 :                              # IMP RTS
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.PC = self.readMem(0x100 + self.SP)
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.PC |= self.readMem(0x100 + self.SP) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x61 :                            # IZX ADC
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x65 :                            # ZPG ADC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x66 :                            # ZPG ROR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (value8 >> 1) | (self.C << 7)
                                    self.C = (value8 & 0x1) != 0
                                    value16 &= 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 5
                                    continue
                            else :
                                # 0x68 to 0x6F

                                if inst ==  0x68 :                              # IMP PLA
                                    self.SP = (self.SP + 1) & 0xFF
                                    self.A = self.readMem(0x100 + self.SP)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x69 :                            # IMM ADC
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x6A :                            # ACC ROR
                                    value16 = (self.A >> 1) | (self.C << 7)
                                    self.C = (self.A & 0x1) != 0
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x6C :                            # IND JMP
                                    address = self.readMem(self.PC) | self.readMem(self.PC + 1) << 8
                                    self.PC = self.readMem(address) | (self.readMem(address + 1) << 8)
                                    clock.ticks += 5
                                    continue

                                elif inst ==  0x6D :                            # ABS ADC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x6E :                            # ABS ROR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (value8 >> 1) | (self.C << 7)
                                    self.C = (value8 & 0x1) != 0
                                    value16 = value16 & 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 6
                                    continue

                        else :
                            if inst < 0x78 :
                            # 0x70 to 0x77

                                if inst ==  0x70 :                              # REL BVS
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if self.V :
                                        clock.ticks += 1
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x71 :                            # IZY ADC
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 1
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    address = (address + self.Y) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 5
                                    continue

                                elif inst ==  0x75 :                            # ZPX ADC
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x76 :                            # ZPX ROR
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (value8 >> 1) | (self.C << 7)
                                    self.C = (value8 & 0x1) != 0
                                    value16 = value16 & 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 6
                                    continue

                            else :
                                # 0x78 to 0x7F

                                if inst ==  0x78 :                              # IMP SEI
                                    self.I = 1
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x79 :                            # ABY ADC
                                    if (self.readMem(self.PC) + self.Y) & 0xFF00 :
                                        clock.ticks += 1
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D:
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x7D :                            # ABX ADC
                                    if (self.readMem(self.PC) + self.X) & 0xFF00 :
                                        clock.ticks += 1
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x7E :                            # ABX ROR
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value16 = (value8 >> 1) | (self.C << 7)
                                    self.C = (value8 & 0x1) != 0
                                    value16 = value16 & 0xFF
                                    self.writeMem(address, value16)
                                    self.Z = value16 == 0
                                    self.S = value16 > 0x7F
                                    clock.ticks += 7
                                    continue

            else :
                if inst < 0xC0 :
                    if inst < 0xA0 :
                        if inst < 0x90 :
                            if inst < 0x88 :
                            # 0x80 to 0x87

                                if inst ==  0x81 :                              # IZX STA
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    self.writeMem(address, self.A)
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x84 :                            # ZPG STY
                                    self.writeMem(self.readMem(self.PC), self.Y)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x85 :                            # ZPG STA
                                    self.writeMem(self.readMem(self.PC), self.A)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0x86 :                            # ZPG STX
                                    self.writeMem(self.readMem(self.PC), self.X)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    clock.ticks += 3
                                    continue

                            else :
                                # 0x88 to 0x8F

                                if inst ==  0x88 :                              # IMP DEY
                                    self.Y = (self.Y - 1) & 0xFF
                                    self.Z = (self.Y & 0xFF) == 0
                                    self.S = (self.Y & self.SIGN) != 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x8A :                            # IMP TXA
                                    self.A = self.X
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x8C :                            # ABS STY
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.writeMem(address, self.Y)
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x8D :                            # ABS STA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.writeMem(address, self.A)
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x8E :                            # ABS STX
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.writeMem(address, self.X)
                                    clock.ticks += 4
                                    continue

                        else :
                            if inst < 0x98 :
                            # 0x90 to 0x97

                                if inst ==  0x90 :                              # REL BCC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if not self.C  :
                                        clock.ticks += 1
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x91 :                            # IZY STA
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    address = (address + self.Y) & 0xFFFF
                                    self.writeMem(address, self.A)
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0x94 :                            # ZPX STY
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.writeMem(address, self.Y)
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x95 :                            # ZPX STA
                                    self.writeMem((self.readMem(self.PC) + self.X) & 0xFF, self.A)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0x96 :                            # ZPY STX
                                    self.writeMem((self.readMem(self.PC) + self.Y) & 0xFF, self.X)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    clock.ticks += 4
                                    continue

                            else :
                                # 0x98 to 0x9F

                                if inst ==  0x98 :                              # IMP TYA
                                    self.A = self.Y
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x99 :                            # ABY STA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    self.writeMem(address, self.A)
                                    clock.ticks += 5
                                    continue

                                elif inst ==  0x9A :                            # IMP TXS
                                    self.SP = self.X
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0x9D :                            # ABX STA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    self.writeMem(address, self.A)
                                    clock.ticks += 5
                                    continue

                    else :
                        if inst < 0xB0 :
                            if inst < 0xA8 :
                            # 0xA0 to 0xA7

                                if inst ==  0xA0 :                              # IMM LDY
                                    self.Y = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.Y == 0
                                    self.S = self.Y > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xA1 :                            # IZX LDA
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    self.A = self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0xA2 :                            # IMM LDX
                                    address = self.PC
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.X = self.readMem(address)
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xA4 :                            # ZPG LDY
                                    self.Y = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.Y == 0
                                    self.S = self.Y > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0xA5 :                            # ZPG LDA
                                    self.A = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0xA6 :                            # ZPG LDX
                                    self.X = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 3
                                    continue

                            else :
                                # 0xA8 to 0xAF

                                if inst ==  0xA8 :                              # IMP TAY
                                    self.Y = self.A
                                    self.Z = self.Y == 0
                                    self.S = self.Y > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xA9 :                            # IMM LDA
                                    self.A = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xAA :                            # IMP TAX
                                    self.X = self.A
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xAC :                            # ABS LDY
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Y = self.readMem(address)
                                    self.Z = self.Y == 0
                                    self.S = self.Y > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xAD :                            # ABS LDA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A = self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xAE :                            # ABS LDX
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.X = self.readMem(address)
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 4
                                    continue

                        else :
                            if inst < 0xB8 :
                            # 0xB0 to 0xB7

                                if inst ==  0xB0 :                              # REL BCS
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if self.C :
                                        clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xB1 :                            # IZY LDA
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    self.A = self.readMem((address + self.Y) & 0xFFFF)
                                    if ((address & 0xFF) + self.Y) & 0xFF00 :
                                        clock.ticks += 6
                                    else :
                                        clock.ticks += 5
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0xB4 :                            # ZPX LDY
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Y = self.readMem(address)
                                    self.Z = self.Y == 0
                                    self.S = self.Y > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xB5 :                            # ZPX LDA
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.A = self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xB6 :                            # ZPY LDX
                                    address = (self.readMem(self.PC) + self.Y) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.X = self.readMem(address)
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 4
                                    continue

                            else :
                                # 0xB8 to 0xBF

                                if inst ==  0xB8 :                              # IMP CLV
                                    self.V = 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xB9 :                            # ABY LDA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    self.A = self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0xBA :                            # IMP TSX
                                    self.X = self.SP
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xBC :                            # ABX LDY
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    self.Y = self.readMem(address)
                                    self.Z = self.Y == 0
                                    self.S = self.Y > 0x7F
                                    continue

                                elif inst ==  0xBD :                            # ABX LDA
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    self.A = self.readMem(address)
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    continue

                                elif inst ==  0xBE :                            # ABY LDX
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    self.X = self.readMem(address)
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    continue

                else :
                    if inst < 0xE0 :
                        if inst < 0xD0 :
                            if inst < 0xC8 :
                            # 0xC0 to  0xC7

                                if inst ==  0xC0 :                              # IMM CPY
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = ((self.Y - value8) & 0xFF) == 0
                                    self.S = ((self.Y - value8) & self.SIGN) != 0
                                    self.C = (self.Y >= value8) != 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xC1 :                            # IZX CMP
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    value8 = self.readMem(address)
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0xC4 :                            # ZPG CPY
                                    value8 = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = ((self.Y - value8) & 0xFF) == 0
                                    self.S = ((self.Y - value8) & self.SIGN) != 0
                                    self.C = (self.Y >= value8) != 0
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0xC5 :                            # ZPG CMP
                                    value8 = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0xC6 :                            # ZPG DEC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 - 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 5
                                    continue

                            else :
                                # 0xC8 to 0xCF

                                if inst ==  0xC8 :                              # IMP INY
                                    self.Y = (self.Y + 1) & 0xFF
                                    self.Z = self.Y  == 0
                                    self.S = self.Y > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xC9 :                            # IMM CMP
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xCA :                            # IMP DEX
                                    self.X = (self.X - 1) & 0xFF
                                    self.Z = (self.X & 0xFF) == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xCC :                            # ABS CPY
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.Y - value8) & 0xFF) == 0
                                    self.S = ((self.Y - value8) & self.SIGN) != 0
                                    self.C = (self.Y >= value8) != 0
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xCD :                            # ABS CMP
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xCE :                            # ABS DEC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 - 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 3
                                    continue

                        else :
                            if inst < 0xD8 :
                            # 0xD0 to 0xD7

                                if inst ==  0xD0 :                              # REL BNE
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if not self.Z :
                                        clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xD1 :                            # IZY CMP
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 6
                                    else :
                                        clock.ticks += 5
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    address = (address + self.Y) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    continue

                                elif inst ==  0xD5 :                            # ZPX CMP
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xD6 :                            # ZPX DEC
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 - 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 6
                                    continue

                            else :
                                # 0xD8 to 0xDF

                                if inst ==  0xD8 :                              # IMP CLD
                                    self.D = 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xD9 :                            # ABY CMP
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    continue

                                elif inst ==  0xDD :                            # ABX CMP
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 5
                                    else :
                                        clock.ticks += 4
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.A - value8) & 0xFF) == 0
                                    self.S = ((self.A - value8) & self.SIGN) != 0
                                    self.C = (self.A >= value8) != 0
                                    continue

                                elif inst ==  0xDE :                            # ABX DEC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 - 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = (value8 & self.SIGN) != 0
                                    clock.ticks += 7
                                    continue

                    else :
                        if inst < 0xF0 :
                            if inst < 0xE8 :
                            # 0xE0 to 0xE7

                                if inst ==  0xE0 :                              # IMM CPX
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = ((self.X - value8) & 0xFF) == 0
                                    self.S = ((self.X - value8) & self.SIGN) != 0
                                    self.C = (self.X >= value8) != 0
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xE1 :                            # IZX SBC
                                    value8 = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    value8 = self.readMem(address)
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 6
                                    continue

                                elif inst ==  0xE4 :                            # ZPG CPX
                                    value8 = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    self.Z = ((self.X - value8) & 0xFF) == 0
                                    self.S = ((self.X - value8) & self.SIGN) != 0
                                    self.C = (self.X >= value8) != 0
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0xE5 :                            # ZPG SBC
                                    value8 = self.readMem(self.readMem(self.PC))
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 3
                                    continue

                                elif inst ==  0xE6 :                            # ZPG INC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = (self.readMem(address) + 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 5
                                    continue

                            else :

                                if inst ==  0xE8 :                              # IMP INX
                                    self.X = (self.X + 1) & 0xFF
                                    self.Z = self.X == 0
                                    self.S = self.X > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xE9 :                            # IMM SBC
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xEA :                            # IMP NOP
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xEC :                            # ABS CPX
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    self.Z = ((self.X - value8) & 0xFF) == 0
                                    self.S = ((self.X - value8) & self.SIGN) != 0
                                    self.C = (self.X >= value8) != 0
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xED :                            # ABS SBC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xEE :                            # ABS INC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 + 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 6
                                    continue

                        else :
                            if inst < 0xF8 :
                            # 0xF0 to 0xF7

                                if inst ==  0xF0 :                              # REL BEQ
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if self.Z :
                                        clock.ticks += 1
                                        if address & self.SIGN :
                                            address |= 0xFF00
                                        if ((self.PC & 0xFF) + address) & 0xFF00 :
                                            clock.ticks += 1
                                        self.PC = (self.PC + address) & 0xFFFF
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xF1 :                            # IZY SBC
                                    value8 = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = self.readMem(value8)
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 1
                                    value8 = (value8 + 1) & 0xFF
                                    address |= self.readMem(value8) << 8
                                    address = (address + self.Y) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 5
                                    continue

                                elif inst ==  0xF5 :                            # ZPX SBC
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xF6 :                            # ZPX INC
                                    address = (self.readMem(self.PC) + self.X) & 0xFF
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 + 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 6
                                    continue

                            else :
                                # 0xF8 to 0xFF

                                if inst ==  0xF8 :                              # IMP SED
                                    self.D = 1
                                    clock.ticks += 2
                                    continue

                                elif inst ==  0xF9 :                            # ABY SBC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.Y) & 0xFF00 :
                                        clock.ticks += 1
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.Y) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C = value16 > 0xFF
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xFD :                            # ABX SBC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    if (address + self.X) & 0xFF00 :
                                        clock.ticks += 1
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 ^= 0xFF
                                    if self.D :
                                        value8 -= 0x0066
                                    value16 = (self.A + value8 + self.C) & 0xFFFF
                                    self.V = ((value16 ^ self.A) & (value16 ^ value8) & 0x0080) != 0
                                    if self.D :
                                        value16 += ((((value16 + 0x66) ^ self.A ^ value8) >> 3) & 0x22) * 3
                                    self.C =  (value16 & 0xFF00) != 0
                                    self.A = value16 & 0xFF
                                    self.Z = self.A == 0
                                    self.S = self.A > 0x7F
                                    clock.ticks += 4
                                    continue

                                elif inst ==  0xFE :                            # ABX INC
                                    address = self.readMem(self.PC)
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address |= self.readMem(self.PC) << 8
                                    self.PC = (self.PC + 1) & 0xFFFF
                                    address = (address + self.X) & 0xFFFF
                                    value8 = self.readMem(address)
                                    value8 = (value8 + 1) & 0xFF
                                    self.writeMem(address, value8)
                                    self.Z = value8 == 0
                                    self.S = value8 > 0x7F
                                    clock.ticks += 7
                                    continue

        return(self.PC)
