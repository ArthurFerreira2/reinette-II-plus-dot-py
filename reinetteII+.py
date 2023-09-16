import sys, os
import ctypes
from sdl2 import *                                                              # pip install pysdl2 pysdl2-dll
import puce6502, memory, keyctrl, screen, speaker, paddle, disk, clock

# import cProfile
# from pstats import Stats, SortKey
# profiler = cProfile.Profile()
# profiler.enable()



helpMsg = b"""
          reinette II plus dot py

Drag'n'drop a .nib file to load a floppy

F1   : this help
F2   : take a screenshot
F3   : paste text from clipboard
F4   : mute / unmute sound
F5   : toggle monochrome (in HGR only)
F6   : decrease zoom down to 1:1
F7   : increase zoom up to 8:1
F8   : decrease desired FPS
F9   : increase desired FPS
F10  : toggle pause
F11  : here is your RESET key
F12  : power cycle

Joystick : 1,2,3 and 5 on keypad.
           CTRL and ALT for the buttons


More at github.com/ArthurFerreira2
"""


#============================================ CPU AND PERIPHERALS INITIALIZATION

screen  = screen.Screen()                                                       # must be instanciated before speaker as it inits SDL2
speaker = speaker.Speaker()
paddle0 = paddle.Paddle()                                                       # x-axis : numpad 1 and 3, push button : CTRL
paddle1 = paddle.Paddle()                                                       # y-axis : numpad 2 and 5, push button : ALT
keyctrl = keyctrl.Keyctrl()                                                     # keyboard controller

disk = disk.Disk()                                                              # instanciate one disk drive
if len(sys.argv) > 1 :                                                          # load floppy if provided at command line
    disk.insertFloppy(sys.argv[1])

mem = memory.Memory(disk, keyctrl, paddle0, paddle1, screen, speaker)           # memory has side effects on peripherals through soft swiches
cpu = puce6502.Puce6502(mem.readMem, mem.writeMem)                              # cpu instantiation with pointer to functions to read and write  memory


#===================================================================== MAIN LOOP

running = True
paused  = False
event = SDL_Event()

while running :

    #=================================================== PROCESS SOME CPU CYCLES

    if not paused :
        cpu.run(clock.CPU_FREQUENCY / screen.FPS)                               # execute instructions until we reach the number clock cycles for one frame

    limit = 50
    while disk.getMotorOn() and limit :                                         # OVERCLOCKING CPU during disk access
        cpu.run(10000)                                                          # execute instruction during 10000 extra clock cyles
        limit-=1                                                                # allow key inputs and screen refresh in case the motor won't stop

    #============================================================== UPDATE VIDEO

    screen.update(mem.ram)                                                      # refresh screen

    #==================================================== CATCH USER INTERACTION

    while SDL_PollEvent(ctypes.byref(event)) :

        alt   = SDL_GetModState() & KMOD_ALT
        ctrl  = SDL_GetModState() & KMOD_CTRL
        shift = SDL_GetModState() & KMOD_SHIFT

        paddle0.setButton(alt)                                                  # update push button 0 state
        paddle1.setButton(ctrl)                                                 # update push button 1 state

        #================================================== QUIT ON WINDOW CLOSE

        if event.type == SDL_QUIT :                                             # Window Manager sent TERM signal
            running = False

        #==================================== LOAD A FLOPPY IMAGE ON DRAG'N DROP

        elif event.type == SDL_DROPFILE :                                       # user dropped a file
            filename = event.drop.file                                          # get its full pathname
            disk.insertFloppy(filename)                                         # load the .nib into memory
            floppyName = os.path.basename(filename[:-4]).decode('utf-8')        # extracting name from filename, removing the .nib extention
            if floppyName.find('(') == -1 :
                screen.setWindowTitle("nib", floppyName)                        # adding name to title, removing anygthing after the first '('
            else :
                screen.setWindowTitle("nib", floppyName[:floppyName.find('(')])     # adding name to title, removing anygthing after the first '('
            SDL_free(filename)                                                  # free filename memory
            paused = False                                                      # might already be the case
            mem.writeMem(0x03F4, 0)                                             # unset the Power-UP byte
            cpu.rst()                                                           # and do a cold reset

        # ================================================= APPLICATION CONTROLS

        elif event.type == SDL_KEYDOWN :                                        # a key has been pressed down

            if event.key.keysym.sym == SDLK_F1 :                                # F1 -> help box
                SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_INFORMATION,b"Help",helpMsg, None)

            elif event.key.keysym.sym == SDLK_F2 :                              # F2 -> take a screenshot
                screen.takeScreenshot()

            elif event.key.keysym.sym == SDLK_F3 :                              # F3 -> paste text from clipboard
                if SDL_HasClipboardText() :
                    clipboardText = SDL_GetClipboardText()
                    for c in clipboardText :                                    # process char by char
                        keyctrl.setKey(0x8D if c == 0x0A else c | 0x80)         # translates Line Feed to Carriage Return and sets bit 7 on
                    SDL_free(clipboardText)                                     # release the ressource

            elif event.key.keysym.sym == SDLK_F4 :                              # F4 -> toggle mute
                speaker.toggleMute()

            elif event.key.keysym.sym == SDLK_F5 :                              # F5 -> toggle monochrome mode
                screen.toggleMonochrome()

            elif event.key.keysym.sym == SDLK_F6 :                              # F6 -> decrease window size
                screen.setZoom(-1)

            elif event.key.keysym.sym == SDLK_F7 :                              # F7 -> increase window size
                screen.setZoom(+1)

            elif event.key.keysym.sym == SDLK_F8 :                              # F8 -> decrease target FPS
                screen.FPS -= 1

            elif event.key.keysym.sym == SDLK_F9 :                              # F9 -> increase target FPS
                screen.FPS += 1

            elif event.key.keysym.sym == SDLK_F10 :
                paused = not paused                                             # F10 -> toggle pause
                screen.setWindowTitle("paused", paused)

            elif event.key.keysym.sym == SDLK_F11 :
                cpu.rst()                                                       # F11 -> reset the cpu

            elif event.key.keysym.sym == SDLK_F12 :                             # F12 -> power cycle
                mem.writeMem(0x3F4, 0)                                          # unset the Power-UP byte
                cpu.rst()

            #================================================= EMULATED KEYBOARD

            keyctrl.setKeyFromKeySym(event.key.keysym.sym,
                                     (1 if ctrl else 0) + (2 if shift else 0))  # taking into account the key modifiers

            #================================================= EMULATED JOYSTICK

            if   event.key.keysym.sym == SDLK_KP_1 :                            # hold pdl0 <-
                paddle0.update(0)
            elif event.key.keysym.sym == SDLK_KP_3 :                            # hold pdl0 ->
                paddle0.update(255)
            elif event.key.keysym.sym == SDLK_KP_5 :                            # hold pdl1 <-
                paddle1.update(0)
            elif event.key.keysym.sym == SDLK_KP_2 :                            # hold pdl1 ->
                paddle1.update(255)

        elif event.type == SDL_KEYUP :
            if   event.key.keysym.sym == SDLK_KP_1 :                            # release pdl0 ->
                paddle0.update(127)
            elif event.key.keysym.sym == SDLK_KP_3 :                            # release pdl0 <-
                paddle0.update(127)
            elif event.key.keysym.sym == SDLK_KP_5 :                            # release pdl1 ->
                paddle1.update(127)
            elif event.key.keysym.sym == SDLK_KP_2 :                            # release pdl1 <-
                paddle1.update(127)


# profiler.disable()

# stream = open('profilingStats.txt', 'w')
# stats = Stats(profiler, stream = stream)

# stats.strip_dirs()
# stats.sort_stats('time')
# stats.dump_stats('prof_stats.dump')                                             # snakeviz.exe prof_stats.dump
# stats.print_stats()

# stream.close()
