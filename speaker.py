from sdl2 import audio                                                          # pip install pysdl2
import ctypes
import clock

class Speaker() :
    """
    emulates the audio speaker of the apple II

    Uses basic sdl audio (not using the SLD_audio lib)
    SDL_Init(SDL_INIT_AUDIO) has to be executed before the instanciation
    """

    BUFFER_LENGHT = 4096                                                        # found to be large enought
    FREQUENCY = 96000                                                           # sample frequency of the audio device
    CPU_CLOCK = 1023000
    RATE = CPU_CLOCK / FREQUENCY


    def __init__(self) :
        """
        initialise the sdl2 audio device and allocate buffers

        allocate 3 buffers for the -volume, 0 and +volumes values
        inits sdl audio devices, signed 8 bits, 96KHz ...
        set pause (muted) to False
        """

        self.buffer = []                                                        # three audio buffers,
        self.buffer.append((ctypes.c_int * Speaker.BUFFER_LENGHT)())            # one used when SPKR is 0
        self.buffer.append((ctypes.c_int * Speaker.BUFFER_LENGHT)())            # the other when SPKR is 1
        self.buffer.append((ctypes.c_int * Speaker.BUFFER_LENGHT)())            # silence, when speaker hasn't been switched for a while

        self.muted = False                                                      # mute/unmute switch
        self.volume = 32
        for i in range(0, Speaker.BUFFER_LENGHT) :
            self.buffer[0][i] = -self.volume
            self.buffer[1][i] = +self.volume
            self.buffer[2][i] = 0

        self.previousTick = clock.ticks                                         # holds the previous ticks value
        self.SPKR = 1                                                           # $C030 Speaker toggle

        self.desired = audio.SDL_AudioSpec(0, 0, 0, 0)                          # Jeez, why have I done this ? I'm not changing it now ...
        self.desired.freq = Speaker.FREQUENCY
        self.desired.format = audio.AUDIO_S8                                    # signed 8 bits
        self.desired.channels = 1                                               # mono
        self.desired.samples = 512

        self.device=audio.SDL_OpenAudioDevice(None,0,self.desired,None,False)   # get the audio device ID
        audio.SDL_PauseAudioDevice(self.device, False)                          # unmute it


    def toggleMute(self) :
        self.muted = not self.muted


    def playSound(self) :
        """
        plays sound

        calculates the time elapsed since the last speaker toggle
        if that time is too long, plays silence
        otherwise plays a positive or negative square wave
        """

        self.SPKR = 0 if self.SPKR else 1                                       # toggle speaker state
        length = int((clock.ticks - self.previousTick) / Speaker.RATE)          # lenght of the square wave
        self.previousTick = clock.ticks

        if not self.muted :
            if length > Speaker.BUFFER_LENGHT :
                audio.SDL_QueueAudio(self.device, self.buffer[2], Speaker.BUFFER_LENGHT)  # silence
            else :
                audio.SDL_QueueAudio(self.device, self.buffer[self.SPKR], length)
