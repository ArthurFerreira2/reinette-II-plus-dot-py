from sdl2 import keycode

class Keyctrl() :

    KEYMAP = {   # MODIFIERS : [None, CTRL, SHFT, BOTH]                         # QWERTY US
    keycode.SDLK_a           : [0xC1, 0x81, 0x00, 0x00],
    keycode.SDLK_b           : [0xC2, 0x82, 0x00, 0x00],
    keycode.SDLK_c           : [0xC3, 0x83, 0x00, 0x00],
    keycode.SDLK_d           : [0xC4, 0x84, 0x00, 0x00],
    keycode.SDLK_e           : [0xC5, 0x85, 0x00, 0x00],
    keycode.SDLK_f           : [0xC6, 0x86, 0x00, 0x00],
    keycode.SDLK_g           : [0xC7, 0x87, 0x00, 0x00],
    keycode.SDLK_h           : [0xC8, 0x88, 0x00, 0x00],
    keycode.SDLK_i           : [0xC9, 0x89, 0x00, 0x00],
    keycode.SDLK_j           : [0xCA, 0x8A, 0x00, 0x00],
    keycode.SDLK_k           : [0xCB, 0x8B, 0x00, 0x00],
    keycode.SDLK_l           : [0xCC, 0x8C, 0x00, 0x00],
    keycode.SDLK_m           : [0xCD, 0x8D, 0x00, 0x9D],
    keycode.SDLK_n           : [0xCE, 0x8E, 0x00, 0x9E],
    keycode.SDLK_o           : [0xCF, 0x8F, 0x00, 0x00],
    keycode.SDLK_p           : [0xD0, 0x80, 0x00, 0x90],
    keycode.SDLK_q           : [0xD1, 0x91, 0x00, 0x00],
    keycode.SDLK_r           : [0xD2, 0x92, 0x00, 0x00],
    keycode.SDLK_s           : [0xD3, 0x93, 0x00, 0x00],
    keycode.SDLK_t           : [0xD4, 0x94, 0x00, 0x00],
    keycode.SDLK_u           : [0xD5, 0x95, 0x00, 0x00],
    keycode.SDLK_v           : [0xD6, 0x96, 0x00, 0x00],
    keycode.SDLK_w           : [0xD7, 0x97, 0x00, 0x00],
    keycode.SDLK_x           : [0xD8, 0x98, 0x00, 0x00],
    keycode.SDLK_y           : [0xD9, 0x99, 0x00, 0x00],
    keycode.SDLK_z           : [0xDA, 0x9A, 0x00, 0x00],
    keycode.SDLK_0           : [0xB0, 0x00, 0xA9, 0x00],
    keycode.SDLK_1           : [0xB1, 0x00, 0xA1, 0x00],
    keycode.SDLK_2           : [0xB2, 0x00, 0xC0, 0x00],
    keycode.SDLK_3           : [0xB3, 0x00, 0xA3, 0x00],
    keycode.SDLK_4           : [0xB4, 0x00, 0xA4, 0x00],
    keycode.SDLK_5           : [0xB5, 0x00, 0xA5, 0x00],
    keycode.SDLK_6           : [0xB6, 0x00, 0xDE, 0x00],
    keycode.SDLK_7           : [0xB7, 0x00, 0xA6, 0x00],
    keycode.SDLK_8           : [0xB8, 0x00, 0xAA, 0x00],
    keycode.SDLK_9           : [0xB9, 0x00, 0xA8, 0x00],
    keycode.SDLK_LEFTBRACKET : [0xDB, 0x9B, 0x00, 0x00],
    keycode.SDLK_BACKSLASH   : [0xDC, 0x9C, 0x00, 0x00],
    keycode.SDLK_RIGHTBRACKET: [0xDD, 0x9D, 0x00, 0x00],
    keycode.SDLK_BACKSPACE   : [0x88, 0xDF, 0x00, 0x00],
    keycode.SDLK_LEFT        : [0x88, 0x00, 0x00, 0x00],
    keycode.SDLK_RIGHT       : [0x95, 0x00, 0x00, 0x00],
    keycode.SDLK_SPACE       : [0xA0, 0x00, 0x00, 0x00],
    keycode.SDLK_ESCAPE      : [0x9B, 0x00, 0x00, 0x00],
    keycode.SDLK_RETURN      : [0x8D, 0x00, 0x00, 0x00],
    keycode.SDLK_QUOTE       : [0xA7, 0x00, 0xA2, 0x00],
    keycode.SDLK_EQUALS      : [0xBD, 0x00, 0xAB, 0x00],
    keycode.SDLK_SEMICOLON   : [0xBB, 0x00, 0xBA, 0x00],
    keycode.SDLK_COMMA       : [0xAC, 0x00, 0xBC, 0x00],
    keycode.SDLK_PERIOD      : [0xAE, 0x00, 0xBE, 0x00],
    keycode.SDLK_SLASH       : [0xAF, 0x00, 0xBF, 0x00],
    keycode.SDLK_MINUS       : [0xAD, 0x00, 0xDF, 0x00],
    keycode.SDLK_BACKQUOTE   : [0xE0, 0x00, 0xFE, 0x00]}


    """
        The Apple II didn't had a key buffer.
        I'm using one for two reasons :
        - let the cpu catch all key pressed as input and cpu execution are desynchronized
        - to allow copy paste : I emit all characters as if they were typed on the keyboard
    """

    def __init__(self) :
        self.keyQueue = []
        self.key = 0x00


    def setKey(self, value) :
        self.keyQueue.append(value)


    def setKeyFromKeySym(self, keySym, modifiers) :
        if keySym in Keyctrl.KEYMAP :
            self.keyQueue.append(Keyctrl.KEYMAP[keySym][modifiers])


    def getKey(self) :                                                          # softswitch $C000
        if len(self.keyQueue) :
            if self.keyQueue[0] <= 0x7F :
                self.key = self.keyQueue.pop(0)
            else :
                self.key = self.keyQueue[0]
        return self.key


    def strobe(self) :                                                          # softswitch $C010
        if len(self.keyQueue) :
            self.keyQueue[0] &= 0x7F
