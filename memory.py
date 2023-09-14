class Memory() :

    #============================================================ SOME CONSTANTS

    RAMSIZE  = 0xC000                                                           # RAM

    ROMSTART = 0xD000                                                           # ROM
    ROMSIZE  = 0x3000

    LGCSTART = 0xD000                                                           # language card
    LGCSIZE  = 0x3000
    BK2START = 0xD000                                                           # bank 2
    BK2SIZE  = 0x1000

    SL6START = 0xC600                                                           # disk ][ prom in slot 6
    SL6SIZE  = 0x0100

    #============================================================ INITIALIZATION

    def __init__(self, disk, keyctrl, paddle0, paddle1, screen, speaker) :

        self.disk    = disk
        self.keyctrl = keyctrl
        self.paddle0 = paddle0
        self.paddle1 = paddle1
        self.screen  = screen
        self.speaker = speaker

        self.LCWR  = True                                                       # Language Card writable
        self.LCRD  = False                                                      # Language Card readable
        self.LCBK2 = True                                                       # Language Card bank 2 enabled
        self.LCWFF = False                                                      # Language Card pre-write flip flop
        self.DLATCH   = 0                                                       # disk ][ one nibble register

        self.ram = bytearray(Memory.RAMSIZE)                                    # 48K of ram in $000-$BFFF
        self.rom = bytearray(Memory.ROMSIZE)                                    # 12K of rom in $D000-$FFFF
        self.lgc = bytearray(Memory.LGCSIZE)                                    # Language Card 12K in $D000-$FFFF
        self.bk2 = bytearray(Memory.BK2SIZE)                                    # bank 2 of Language Card 4K in $D000-$DFFF
        self.sl6 = bytearray(Memory.SL6SIZE)                                    # P5A disk ][ prom in slot 6

        open('assets/appleII+.rom', 'rb').readinto(self.rom)                    # load APPLESOFT ROM
        open('assets/diskII.rom',   'rb').readinto(self.sl6)                    # load disk ][ PROM


    #======================================= MEMORY MAPPED SOFT SWITCHES HANDLER

    def softSwitches(self, address, value = None) :
        """ this function is called from readMem and writeMem

            it complements both functions when address is in page $C0
        """
        if address < 0xC080 :
            if address < 0xC050 :
                if address == 0xC020 or address == 0xC030 :                     # SPEAKER, TAPEOUT
                    self.speaker.playSound()
                elif address == 0xC000 :                                        # KEYBOARD
                    return self.keyctrl.getKey()
                elif address == 0xC010 :                                        # KBDSTROBE
                    self.keyctrl.strobe()
                    return self.keyctrl.getKey()
            elif address < 0xC060 :
                if address == 0xC050 :                                          # Graphics
                    self.screen.setTEXT(False)
                elif address == 0xC051 :                                        # Text
                    self.screen.setTEXT(True)
                elif address == 0xC052 :                                        # Mixed off
                    self.screen.setMIXED(False)
                elif address == 0xC053 :                                        # Mixed on
                    self.screen.setMIXED(True)
                elif address == 0xC054 :                                        # PAGE2 off
                    self.screen.setPAGE2(False)
                elif address == 0xC055 :                                        # PAGE2 on
                    self.screen.setPAGE2(True)
                elif address == 0xC056 :                                        # HiRes off
                    self.screen.setHIRES(False)
                elif address == 0xC057 :                                        # HiRes on
                    self.screen.setHIRES(True)
            else:
                if address == 0xC061 :                                          # Push Button 0
                    return self.paddle0.getButton()
                elif address == 0xC062 :                                        # Push Button 1
                    return self.paddle1.getButton()
                elif address == 0xC064 :                                        # Paddle 0
                    return self.paddle0.read()
                elif address == 0xC065 :                                        # Paddle 1
                    return self.paddle1.read()
                elif address == 0xC070 :                                        # paddle timer RST
                    self.paddle0.reset()
                    self.paddle1.reset()

        else :
            if address < 0xC0E0 :
                if address == 0xC080 or address == 0xC084 :                     # LC2RD
                    self.LCBK2 = True
                    self.LCRD = True
                    self.LCWR = False
                    self.LCWFF = False
                elif address == 0xC081 or address == 0xC085 :                   # LC2WR
                    self.LCBK2 = True
                    self.LCRD = False
                    self.LCWR |= self.LCWFF
                    self.LCWFF = value is None
                elif address == 0xC082 or address == 0xC086 :                   # ROMONLY2
                    self.LCBK2 = True
                    self.LCRD = False
                    self.LCWR = False
                    self.LCWFF = False
                elif address == 0xC083 or address == 0xC087 :                   # LC2RW
                    self.LCBK2 = True
                    self.LCRD = True
                    self.LCWR |= self.LCWFF
                    self.LCWFF = value is None
                elif address == 0xC088 or address == 0xC08C :                   # LC1RD
                    self.LCBK2 = False
                    self.LCRD = True
                    self.LCWR = False
                    self.LCWFF = False
                elif address == 0xC089 or address == 0xC08D :                   # LC1WR
                    self.LCBK2 = False
                    self.LCRD = False
                    self.LCWR |= self.LCWFF
                    self.LCWFF = value is None
                elif address == 0xC08A or address == 0xC08E :                   # ROMONLY1
                    self.LCBK2 = False
                    self.LCRD = False
                    self.LCWR = False
                    self.LCWFF = False
                elif address == 0xC08B or address == 0xC08F :                   # LC1RW
                    self.LCBK2 = False
                    self.LCRD = True
                    self.LCWR |= self.LCWFF
                    self.LCWFF = value is None
            else :
                if address == 0xC0EC :
                    if self.disk.getWriteMode() :                               # writting dLatch
                        self.disk.write(self.DLATCH)
                        self.screen.setWindowTitle("r/w",
                            f"WRITE[0x{self.disk.track:02X}, 0x{self.disk.nibble:04X}]")
                    else :                                                      # reading dLatch
                        self.DLATCH = self.disk.read()
                        self.screen.setWindowTitle("r/w",
                            f"READ[0x{self.disk.track:02X}, 0x{self.disk.nibble:04X}]")
                    return self.DLATCH
                elif address >= 0xC0E0 and address <= 0xC0E7 :                  # MOVE DRIVE HEAD
                    self.disk.stepMotor(address)
                elif address == 0xC0ED :                                        # Load Data Latch
                    if value :
                        self.DLATCH = value
                elif address == 0xC0EE :                                        # latch for READ
                    self.disk.setWriteMode(False)
                    return 0x80 if self.disk.getReadOnly() else 0x00            # check protection
                elif address == 0xC0EF :                                        # latch for WRITE
                    self.disk.setWriteMode(True)
                elif address == 0xCFFF or address == 0xC0E8 :                   # MOTOROFF
                    self.disk.setMotorOn(False)
                elif address == 0xC0E9 :                                        # MOTORON
                    self.disk.setMotorOn(True)
                elif address == 0xC0EA :                                        # DRIVE0EN (not implemented)
                    pass
                elif address == 0xC0EB :                                        # DRIVE1EN (not implemented)
                    pass

        return 0                                                                # catch all

    #============================================================= MEMORY ACCESS

    def readMem(self, address) :                                                # read
        if address < Memory.RAMSIZE :
            return self.ram[address]                                            # RAM
        if address >= Memory.ROMSTART :
            if not self.LCRD :
                return self.rom[address - Memory.ROMSTART]                      # ROM
            if self.LCBK2 and (address < 0xE000) :
                return self.bk2[address - Memory.BK2START]                      # BK2
            return self.lgc[address - Memory.LGCSTART]                          # LC
        if (address & 0xFF00) == Memory.SL6START :
            return self.sl6[address - Memory.SL6START]                          # disk][
        if (address & 0xF000) == 0xC000 :
            return self.softSwitches(address)                                   # Soft Switches
        return 0                                                                # catch all


    def writeMem(self, address, value) :                                        # write
        if address < Memory.RAMSIZE :
            self.ram[address] = value                                           # RAM
            return
        if self.LCWR and (address >= Memory.ROMSTART) :
            if self.LCBK2 and (address < 0xE000) :
                self.bk2[address - Memory.BK2START] = value                     # BK2
                return
            self.lgc[address - Memory.LGCSTART] = value                         # LC
            return
        if (address & 0xF000) == 0xC000 :
            self.softSwitches(address, value)                                   # Soft Switches
