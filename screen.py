from sdl2 import *                                                              # pip install pysdl2
import ctypes
from datetime import datetime

class Screen() :

    #================================================================= CONSTANTS

    GR_COLOR = [                                                                # the 16 low res colors
        [0,   0,   0  ], [226, 57,  86 ], [28,  116, 205], [126, 110, 173],
        [31,  129, 128], [137, 130, 122], [86,  168, 228], [144, 178, 223],
        [151, 88,  34 ], [234, 108, 21 ], [158, 151, 143], [255, 206, 240],
        [144, 192, 49 ], [255, 253, 166], [159, 210, 213], [255, 255, 255]
    ]

    HGR_COLORS = [                                                              # the high res colors (2 light levels)
        [0,   0,   0  ], [144, 192,  49], [126, 110, 173], [255, 255, 255],
        [0,   0,   0  ], [234, 108,  21], [ 86, 168, 228], [255, 255, 255],
        [0,   0,   0  ], [ 63,  55,  86], [ 72,  96,  25], [255, 255, 255],
        [0,   0,   0  ], [ 43,  84, 114], [117,  54,  10], [255, 255, 255]
    ]

    GR_OFFSET = [                                                               # helper for TEXT and GR video generation
        0x0000, 0x0080, 0x0100, 0x0180, 0x0200, 0x0280, 0x0300, 0x0380,         # lines 0-7
        0x0028, 0x00A8, 0x0128, 0x01A8, 0x0228, 0x02A8, 0x0328, 0x03A8,         # lines 8-15
        0x0050, 0x00D0, 0x0150, 0x01D0, 0x0250, 0x02D0, 0x0350, 0x03D0          # lines 16-23
    ]

    HGR_OFFSET = [                                                              # helper for HGR video generation
        0x0000, 0x0400, 0x0800, 0x0C00, 0x1000, 0x1400, 0x1800, 0x1C00,         # lines 0-7
        0x0080, 0x0480, 0x0880, 0x0C80, 0x1080, 0x1480, 0x1880, 0x1C80,         # lines 8-15
        0x0100, 0x0500, 0x0900, 0x0D00, 0x1100, 0x1500, 0x1900, 0x1D00,         # lines 16-23
        0x0180, 0x0580, 0x0980, 0x0D80, 0x1180, 0x1580, 0x1980, 0x1D80,
        0x0200, 0x0600, 0x0A00, 0x0E00, 0x1200, 0x1600, 0x1A00, 0x1E00,
        0x0280, 0x0680, 0x0A80, 0x0E80, 0x1280, 0x1680, 0x1A80, 0x1E80,
        0x0300, 0x0700, 0x0B00, 0x0F00, 0x1300, 0x1700, 0x1B00, 0x1F00,
        0x0380, 0x0780, 0x0B80, 0x0F80, 0x1380, 0x1780, 0x1B80, 0x1F80,
        0x0028, 0x0428, 0x0828, 0x0C28, 0x1028, 0x1428, 0x1828, 0x1C28,
        0x00A8, 0x04A8, 0x08A8, 0x0CA8, 0x10A8, 0x14A8, 0x18A8, 0x1CA8,
        0x0128, 0x0528, 0x0928, 0x0D28, 0x1128, 0x1528, 0x1928, 0x1D28,
        0x01A8, 0x05A8, 0x09A8, 0x0DA8, 0x11A8, 0x15A8, 0x19A8, 0x1DA8,
        0x0228, 0x0628, 0x0A28, 0x0E28, 0x1228, 0x1628, 0x1A28, 0x1E28,
        0x02A8, 0x06A8, 0x0AA8, 0x0EA8, 0x12A8, 0x16A8, 0x1AA8, 0x1EA8,
        0x0328, 0x0728, 0x0B28, 0x0F28, 0x1328, 0x1728, 0x1B28, 0x1F28,
        0x03A8, 0x07A8, 0x0BA8, 0x0FA8, 0x13A8, 0x17A8, 0x1BA8, 0x1FA8,
        0x0050, 0x0450, 0x0850, 0x0C50, 0x1050, 0x1450, 0x1850, 0x1C50,
        0x00D0, 0x04D0, 0x08D0, 0x0CD0, 0x10D0, 0x14D0, 0x18D0, 0x1CD0,
        0x0150, 0x0550, 0x0950, 0x0D50, 0x1150, 0x1550, 0x1950, 0x1D50,
        0x01D0, 0x05D0, 0x09D0, 0x0DD0, 0x11D0, 0x15D0, 0x19D0, 0x1DD0,
        0x0250, 0x0650, 0x0A50, 0x0E50, 0x1250, 0x1650, 0x1A50, 0x1E50,
        0x02D0, 0x06D0, 0x0AD0, 0x0ED0, 0x12D0, 0x16D0, 0x1AD0, 0x1ED0,         # lines 168-183
        0x0350, 0x0750, 0x0B50, 0x0F50, 0x1350, 0x1750, 0x1B50, 0x1F50,         # lines 176-183
        0x03D0, 0x07D0, 0x0BD0, 0x0FD0, 0x13D0, 0x17D0, 0x1BD0, 0x1FD0          # lines 184-191
    ]

    NORMAL  = 0
    INVERSE = 1
    FLASH   = 2


    def __init__(self) :

        #============================ VARIABLES USED DURING THE VIDEO PRODUCTION

        self.ATTRIBUTES = [ Screen.NORMAL if x>0x7F else Screen.INVERSE if x<0x40 else Screen.FLASH for x in range(0x100)]

        self.TEXT  = True                                                       # $C050 CLRTEXT   / $C051 SETTEXT
        self.MIXED = False                                                      # $C052 CLRMIXED  / $C053 SETMIXED
        self.PAGE2 = False                                                      # $C054 PAGE2 off / $C055 PAGE2 on
        self.HIRES = False                                                      # $C056 GR        / $C057 HGR
        self.currentMode = 0
        self.previousMode = 0

        self.oldMode = currentMode = 0                                          # to flush the video caches on video mode change
        self.TextCache   = [[-1 for x in range(40)] for y in range( 24)]        # video caches
        self.LoResCache  = [[-1 for x in range(40)] for y in range( 24)]
        self.HiResCache  = [[-1 for x in range(40)] for y in range(192)]
        self.previousBit = [[ 0 for x in range(40)] for y in range(192)]

        self.pixelGR = SDL_Rect(0, 0, 7, 4)                                     # a block in LoRes
        self.dstRect = SDL_Rect(0, 0, 7, 8)                                     # the dst character in rdr
        self.charRects = [SDL_Rect(7 * x, 0, 7, 8) for x in  range(0, 128)]     # the src from the norm and rev textures

        self.zoom = 2
        self.monochrome = False

        self.FPS = 20.0
        self.frameStart = 0
        self.frameNumber = 0                                                     # TEXT cursor flashes at 2Hz

        self.title = {"name"   : "reinette II plus dot py    ",                                # update the window title with dynamic data
                      "paused" : "",
                      "fps"    : "0" ,
                      "r/w"    : "",
                      }

        #==================================================== SDL INITIALIZATION

        SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO)
        self.wdo = SDL_CreateWindow(b"reinette II plus dot py",
                                    SDL_WINDOWPOS_CENTERED,
                                    SDL_WINDOWPOS_CENTERED,
                                    280 * self.zoom, 192 * self.zoom,
                                    SDL_WINDOW_OPENGL)

        # FIXME : icon transparency
        self.ico = SDL_LoadBMP(b"assets/icon.bmp")
        SDL_SetWindowIcon(self.wdo, self.ico)

        self.rdr = SDL_CreateRenderer(self.wdo, -1,
                                     SDL_RENDERER_SOFTWARE | SDL_RENDERER_PRESENTVSYNC)

        # SDL_SetRenderDrawBlendMode(self.rdr, SDL_BLENDMODE_NONE)
        SDL_SetRenderDrawBlendMode(self.rdr, SDL_BLENDMODE_BLEND)
        SDL_RenderSetScale(self.rdr, self.zoom, self.zoom)
        SDL_EventState(SDL_DROPFILE, SDL_ENABLE)
        SDL_RenderSetScale(self.rdr, self.zoom, self.zoom)


        #============================ LOAD NORMAL AND REVERSE CHARACTERS BITMAPS

        tmpSurface = SDL_LoadBMP(b"assets/font-normal.bmp")                     # load the normal font
        self.normCharTexture = SDL_CreateTextureFromSurface(self.rdr, tmpSurface)
        SDL_FreeSurface(tmpSurface)

        tmpSurface = SDL_LoadBMP(b"assets/font-reverse.bmp")                    # load the reverse font
        self.revCharTexture = SDL_CreateTextureFromSurface(self.rdr, tmpSurface)
        SDL_FreeSurface(tmpSurface)



    #============================================= DESTRUCTOR : SDL2 TERMINATION

    def __del__(self):
        SDL_DestroyTexture(self.normCharTexture)
        SDL_DestroyTexture(self.revCharTexture)
        SDL_DestroyRenderer(self.rdr)
        SDL_DestroyWindow(self.wdo)
        SDL_AudioQuit()
        SDL_Quit()

    #======================= GETERS AND SETTERS FOR VIDEO RELATED SOFT SWITCHES

    def setTEXT(self, value) :
        self.TEXT = value
        if value :
            self.currentMode = 0
        else :
            self.currentMode = 1

    def getTEXT(self) :
        return self.TEXT


    def setMIXED(self, value) :
        self.MIXED = value
        if value :
            self.currentMode = 2
        else :
            self.currentMode = 3

    def getMIXED(self) :
        return self.MIXED


    def setHIRES(self, value) :
        self.HIRES = value
        if value :
            self.currentMode = 4
        else :
            self.currentMode = 5

    def getHIRES(self) :
        return self.HIRES


    def setPAGE2(self, value) :
        self.PAGE2 = value

    def getPAGE2(self) :
        return self.PAGE2

    #================================================================ SCREENSHOT

    def takeScreenshot(self):
        sshot = SDL_GetWindowSurface(self.wdo)                                  # alocate a new surface
        SDL_RenderReadPixels(self.rdr,                                          # copy the screen into the surface
                             None,
                             SDL_GetWindowPixelFormat(self.wdo) ,
                             ctypes.cast(sshot.contents.pixels,
                                         ctypes.POINTER(Sint16)),
                             280 * 4 * self.zoom)

        d = datetime.now().strftime("%Y-%m-%d-%H-%M-%S").encode('ASCII')        # forge the filename
        SDL_SaveBMP(sshot, b"screenshots//" + d + b".bmp")                      # save under the screenshots folder
        SDL_FreeSurface(sshot)                                                  # release the surface

    #============================================================== WINDOW TITLE

    def setWindowTitle(self, attribute, value) :
        self.title[attribute] = value                                           # update the attribute
        if attribute == "r/w" :
            self.title["fade"] = 15

    def updateWindowTitle(self) :
        title = self.title["name"]

        if self.title["paused"] != "":
            title += self.title["paused"]
            SDL_SetWindowTitle(self.wdo,  bytes(title, 'ascii'))
            return

        title += self.title["fps"] + self.title["r/w"]
        # self.title["fade"] -= 1
        # if self.title["fade"] < 0 :
        self.title["r/w"] = ""

        SDL_SetWindowTitle(self.wdo,  bytes(title, 'ascii'))

    #============================================== TOGGLE MONOCHROME (HGR ONLY)

    def toggleMonochrome(self) :
        self.monochrome = not self.monochrome
        self.oldMode = 9

    #============================================================= WINDOW RESIZE

    def setZoom(self, value) :
        self.zoom += value                                                      # update zoom
        if self.zoom < 1 :
            self.zoom = 1
        if self.zoom > 8 :
            self.zoom = 8

        SDL_SetWindowSize(self.wdo, 280 * self.zoom, 192 * self.zoom)           # update window size
        SDL_RenderSetScale(self.rdr, self.zoom, self.zoom)                      # update renderer size
        self.oldMode = 9                                                        # provoke a video cache flush


    #============================================================ VIDEO RENDERER

    def update(self, ram) :

        #===================================================== CLEAR VIDEO CACHE

        if self.oldMode != self.currentMode :                                   # Clear the video caches on video mode change
            self.TextCache   = [[-1 for x in range(40)] for y in range( 24)]
            self.LoResCache  = [[-1 for x in range(40)] for y in range( 24)]
            self.HiResCache  = [[-1 for x in range(40)] for y in range(192)]
            self.previousBit = [[ 0 for x in range(40)] for y in range(192)]
            self.oldMode = self.currentMode

    #============================================================= HGR VIDEO OUT

        if not self.TEXT and self.HIRES :                                       # HIGH RES GRAPHICS, mixed or not mixed
            bits=[0] * 16
            vRamBase = 0x2000 + self.PAGE2 * 0x2000
            lastLine = 160 if self.MIXED else 192
            colorIdx = 0;                                                       # to index the color arrays

            for line in range(0, lastLine) :                                    # for every line
                for col in range(0, 40, 2) :                                    # for every 7 horizontal dots
                    x = col * 7
                    even = 0
                    addr = vRamBase + Screen.HGR_OFFSET[line] + col             # addr is always even
                    word = (ram[addr + 1] << 8) + ram[addr]                     # store the two next bytes into 'word'

                    if self.HiResCache[line][col] != word :                     # check if this group of 7 dots need a redraw
                        self.HiResCache[line][col] = word                       # update the video cache

                        for bit in range(0, 16) :                               # store all bits 'word' into 'bits'
                            bits[bit] = (word >> bit) & 1
                        colorSet = bits[7] * 4                                  # select the right color set

                        pbit = self.previousBit[line][col]                      # the bit value of the left dot
                        bit = 0                                                 # starting at 1st bit of 1st byte
                        while bit < 15 :                                        # until we reach bit7 of 2nd byte
                            if bit == 7 :                                       # moving into the second byte
                                colorSet = bits[15] * 4                         # update the color set
                                bit += 1                                        # skip bit 7

                            if self.monochrome :
                                colorIdx = bits[bit] * 3                        # black if bit==0, white if bit==1
                            else :
                                colorIdx = even + colorSet + (bits[bit] << 1) + pbit

                            SDL_SetRenderDrawColor(self.rdr,
                                                   Screen.HGR_COLORS[colorIdx][0],
                                                   Screen.HGR_COLORS[colorIdx][1],
                                                   Screen.HGR_COLORS[colorIdx][2],
                                                   SDL_ALPHA_OPAQUE)
                            SDL_RenderDrawPoint(self.rdr, x, line)

                            x += 1
                            pbit = bits[bit]                                    # proceed to the next pixel
                            bit += 1
                            even = 0 if even else 8                             # one pixel every other is darker

                        if (col < 37) :                                         # check color franging effect on the dot after
                            self.previousBit[line][col + 2] = pbit              # set pbit and clear the
                            self.HiResCache[line][col + 2] = -1                 # video cache for next dot

        #========================================================== GR VIDEO OUT

        elif not self.TEXT :                                                    # lOW RES GRAPHICS, mixed or not mixed
            vRamBase = 0x400 + self.PAGE2 * 0x0400
            lastLine = 20 if self.MIXED else 24

            for col in range(0, 40) :                                           # for each column
                self.pixelGR.x = col * 7
                for line in range(0, lastLine) :                                # for each row
                    self.pixelGR.y = line * 8                                   # first block

                    glyph = ram[vRamBase + Screen.GR_OFFSET[line] + col]        # read video memory
                    if (self.LoResCache[line][col] != glyph) :
                        self.LoResCache[line][col] = glyph                      # update the video cache

                        colorIdx = glyph & 0x0F                                 # first nibble
                        SDL_SetRenderDrawColor(self.rdr,
                                               Screen.GR_COLOR[colorIdx][0],
                                               Screen.GR_COLOR[colorIdx][1],
                                               Screen.GR_COLOR[colorIdx][2],
                                               SDL_ALPHA_OPAQUE)
                        SDL_RenderFillRect(self.rdr, self.pixelGR)

                        self.pixelGR.y += 4                                     # second block
                        colorIdx = (glyph & 0xF0) >> 4                          # second nibble
                        SDL_SetRenderDrawColor(self.rdr,
                                               Screen.GR_COLOR[colorIdx][0],
                                               Screen.GR_COLOR[colorIdx][1],
                                               Screen.GR_COLOR[colorIdx][2],
                                               SDL_ALPHA_OPAQUE)
                        SDL_RenderFillRect(self.rdr, self.pixelGR)


        #======================================================== TEXT VIDEO OUT

        if self.TEXT or self.MIXED :                                            # TEXT 40 COLUMNS, can be mixed with lo or hi res
            vRamBase = 0x400 + self.PAGE2 * 0x0400
            firstLine = 0 if self.TEXT else 20
            flashing = self.frameNumber % self.FPS > self.FPS / 2               # flashing on phase

            for col in range(0, 40) :                                           # for each column
                self.dstRect.x = col * 7

                for line in range(firstLine, 24) :                              # for each row
                    self.dstRect.y = line * 8

                    glyph = ram[vRamBase + Screen.GR_OFFSET[line] + col]        # read video memory
                    glyphAttr = self.ATTRIBUTES[glyph]

                    if (glyphAttr == Screen.FLASH) or (self.TextCache[line][col] != glyph) :

                        self.TextCache[line][col] = glyph                       # update the video cache
                        glyph &= 0x7F                                           # unset bit 7
                        if glyph > 0x5F :
                            glyph &= 0x3F                                       # shifts to match the ASCII codes
                        if glyph < 0x20 :
                            glyph |= 0x40

                        if (glyphAttr==Screen.NORMAL) or (glyphAttr==Screen.FLASH and flashing) :
                            SDL_RenderCopy(self.rdr, self.normCharTexture,
                                           self.charRects[glyph], self.dstRect)
                        else :                                                  # it"s reverse of flashing off
                            SDL_RenderCopy(self.rdr, self.revCharTexture,
                                           self.charRects[glyph], self.dstRect)


    #============================================= SYNC TO FPS AND RENDER SCREEN

        self.frameNumber = (self.frameNumber + 1) % self.FPS                    # for flashing characters (including the cursor)

        frameTime = SDL_GetTicks() - self.frameStart                            # elapsed time since last call
        frameDelay = 1000.0 / self.FPS                                          # target frame time for current FPS
        if frameTime < frameDelay :
            SDL_Delay(int(frameDelay - frameTime))                              # wait until next 1/FPS sec is reached


        if not self.frameNumber % 4 :                                           # update the window title every quarter of a second
            self.setWindowTitle("fps",f"{1000.0 / (SDL_GetTicks() - self.frameStart):05.2f}   ")
            self.updateWindowTitle()

        SDL_RenderPresent(self.rdr)                                             # swap buffers
        self.frameStart = SDL_GetTicks()                                        # start of frame
