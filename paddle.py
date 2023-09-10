import clock

class Paddle() :                                                                # digital controller

    def __init__(self) :
        self.pushButton = 0                                                     # Push Button
        self.position = 127                                                     # Position ranging from 0 (left) to 255 right, 127 is the middle
        self.countdown = 0.0                                                    # Countdown, since reset
        self.countdownTrigger = 0                                               # the cpu tick at which the countdown was reseted


    def getButton(self) :
        return self.pushButton


    def setButton(self, value) :
        self.pushButton = 0xFF if value else 0x00


    def reset(self) :
        self.countdown = self.position * self.position                          # initialize the countdown - depends on the actual position
        self.countdownTrigger = clock.ticks                                     # records the time this was done


    def read(self) :
        self.countdown -= (clock.ticks - self.countdownTrigger) / 5.6           # decreases the countdown
        if self.countdown <= 0 :
            self.countdown = 0                                                  # timeout
            return 0x00                                                         # returns 0
        return 0x80                                                             # not timeout, return something with the MSB set


    def update(self, value) :
        self.position = value


"""
paste this (F3) to check your changes

NEW
10 A =  PDL (0)
20 B =  PDL (1)
30 C =  PEEK (49249) : REM PB0
40 D =  PEEK (49250) : REM PB1
50 PRINT "X:";A;" Y:";B;
60 IF C > 127 THEN  PRINT " 0";
70 IF D > 127 THEN  PRINT " 1";
80 PRINT
90 GOTO 10
RUN

"""
