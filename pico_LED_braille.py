from machine import Pin

STEP = 6
from braille import translate_text


class braille_reader:
    #intialize with list of 6 Pins, char_len
    def __init__(self,pin_list, char_len,line_num=1,text_input=''):
        self.char_len = char_len
        self.line_num = line_num
        self.pin_list = pin_list
        self.cursor = 0
        self.real_text = text_input
        self.braille_text = translate_text(text_input)
        
        if len(self.braille_text) > 0:
            self.show()
        
    def __str__(self):
        return str(vars(self))
        
    #clear current text and reset cursor back to 0
    def take_text_input(self,string):
        self.clear()
        self.real_text = string
        self.braille_text = translate_text(string)
        self.cursor = 0
        self.show()
        
    def show(self):
        #for testing

        braille_snippet = ""
        for i in range(self.cursor,self.cursor+STEP):
            braille_snippet = self.braille_text[i]

        text_snippet = self.real_text[(self.cursor/STEP)]

        print(
            f'{text_snippet} : {braille_snippet}  '
        )


        for i in range(self.cursor,self.cursor+STEP):
            pin_val = int(self.braille_text[i])
            self.pin_list[i - self.cursor].value(pin_val)
 
        #for testing 
        print(f'{self.pin_list[0].value()} {self.pin_list[1].value()} {self.pin_list[2].value()}  {self.pin_list[3].value()}  {self.pin_list[4].value()}  {self.pin_list[5].value()}  ')

    def move(self,direction):
    #direction is either 1 or -1; 1 = right; -1 = left.
        try:
            #reads bitstring and relies on index of bitstring to navigate
            next_cursor = self.cursor + (STEP * self.char_len * direction)
            if next_cursor > -1 and next_cursor < len(self.text_input):
                self.cursor = next_cursor
                self.show()
                
        except Exception as e:
            print(e)
        
    def clear(self):

        #turn all pins to 0
        for pin in self.pin_list:
            self.pin_list.value(0)