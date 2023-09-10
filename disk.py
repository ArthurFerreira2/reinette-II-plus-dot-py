class Disk() :

    # with the invaluable help from :
    # http://www.hackzapple.com/DISKII/DISKIITECH09.HTM
    # http://www.hackzapple.com/DISKII/DISKIITECH09D.HTM

    def __init__(self) :
        self.data = bytearray(232960)                                           # nibblelized disk image
        self.readOnly  = False                                                  # TODO : update it according to actual nib file attributes
        self.motorOn   = False                                                  # motor status
        self.writeMode = False                                                  # writes to file

        self.phases   = [False, False, False, False]                            # 4 x magnets phases states
        self.phasesB  = [False, False, False, False]                            # phases states Before
        self.phasesBB = [False, False, False, False]                            # phases states Before the Before
        self.pIdx     = 0                                                       # phase index
        self.pIdxB    = 0                                                       # phase index Before

        self.track    = 0                                                       # current track position
        self.halfTrk  = 0                                                       # half track position
        self.nibble   = 0                                                       # ptr to self.data : nibble under head position


    #======================= GETERS AND SETTERS FOR DISK][ RELATED SOFT SWITCHES

    def setWriteMode(self, state) :
        self.writeMode = state

    def getWriteMode(self) :
        return self.writeMode

    def setMotorOn(self, state) :
        self.motorOn = state

    def getMotorOn(self) :
        return self.motorOn

    def setReadOnly(self, state) :
        self.readOnly = state

    def getReadOnly(self) :
        return self.readOnly

    #======================================================= LOAD A FLOPPY IMAGE

    def insertFloppy(self, filename) :
        open(filename, 'rb').readinto(self.data)

    #========================================================== READS AND WRITES

    def read(self) :
        self.nibble = (self.nibble + 1) % 0x1A00                                # spins the disk by one nibble before each read
        return self.data[(self.track * 0x1A00) + self.nibble]

    def write(self, value) :
        self.nibble = (self.nibble + 1) % 0x1A00                                # spins the disk by one nibble before each write
        self.data[(self.track * 0x1A00) + self.nibble] = value

    #====================================================== STEPPER MOTOR (HEAD)

    def stepMotor(self, address) :
        address &= 7
        phase = address >> 1

        self.phasesBB[self.pIdxB] = self.phasesB[self.pIdxB]                    # stepper motor
        self.phasesB[self.pIdx]   = self.phases[self.pIdx]                      # keep track of 2 previous phases
        self.pIdxB = self.pIdx                                                  # keep track of the previous indexes (activated phase)
        self.pIdx  = phase

        if not (address & 1) :                                                  # head not moving (PHASE x OFF)
            self.phases[phase] = False
            return

        if self.phasesBB[(phase + 1) & 3] :                                     # head is moving in by half a track
            self.halfTrk -= 1
            if self.halfTrk < 0 :
                self.halfTrk = 0

        if self.phasesBB[(phase - 1) & 3] :                                     # head is moving out by half a track
            self.halfTrk += 1
            if self.halfTrk > 68 :                                              # tracks are numbered from 0 to 34
                self.halfTrk = 68                                               # and half tracks from 0 to 68 (34*2)

        self.phases[phase] = True                                               # update track#
        self.track = (self.halfTrk + 1) // 2                                    # floor division
        self.nibble = 0                                                         # reset nibble as we change track (optionnal, and not always a good optimisation)
