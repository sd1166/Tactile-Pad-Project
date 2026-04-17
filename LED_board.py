from pico_LED_braille import braille_reader
from machine import Pin
from time import sleep_ms


LED_1 = Pin(21, Pin.OUT, value=0)
LED_2 = Pin(20, Pin.OUT, value=0)
LED_3 = Pin(19, Pin.OUT, value=0)
LED_4 = Pin(18, Pin.OUT, value=0)
LED_5 = Pin(17, Pin.OUT, value=0)
LED_6 = Pin(16, Pin.OUT, value=0)
LEDlist = [LED_1,LED_2,LED_3,LED_4,LED_5,LED_6]

LEFT = -1
RIGHT = 1

def send_toLEDboard(text):

    b_read = braille_reader(pin_list=LEDlist,char_len=1,text_input=text)
    while True:
        try:
            #for testing
            keybd = input(f'Braille Reader on Pos:{b_read.cursor}')
            if keybd == 'd':
                sleep_ms(100)
                b_read.move(RIGHT)
            elif keybd == 'a':
                sleep_ms(100)
                b_read.move(LEFT)
            elif keybd == 'i':
                newinput = input('Add in new text')
                sleep_ms(100)
                b_read.take_input(newinput)
        except KeyboardInterrupt:
            b_read.clear()
            break







