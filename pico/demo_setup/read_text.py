'''from ws2812 import WS2812
pin_num = 7
led_strip = WS2812(pin_num, 256)
'''
from time import sleep

DOT_STATUS = [(0, 0, 0),(20, 0, 0)]
READ_STEP = 6
ROW_STEP = 32
CHAR_LIMIT = 16
LINE_OFFSET = 128 

text_repl = ['^','*']

r1 = ['^'] * 256


#initialize row and col for led_strip navigation

def send_to_LEDstrip(bitstr, length):
    row_num = 0
    col_num = 0
    curr_line = 0
    char_len = int(length / READ_STEP)
    
    #clear first
    LEDstrip_clear()
    
    for i in range(0, min(char_len, 32)):
        if i > CHAR_LIMIT:
            curr_line = 1
        #iterates each pin of 6
        for j in range(0, READ_STEP):
            val = int(bitstr[j + (READ_STEP * i)])
            print(f'{val} pin:{j} ch:{i} bitstr index:{j + (READ_STEP) * i} ')
            
            dot_pos = (row_num * ROW_STEP) + col_num 

            dot_pos += (curr_line * LINE_OFFSET)
            
            r1[dot_pos] = text_repl[val]
            #led_strip.pixels_set(dot_pos, DOT_STATUS[val])
            #go to next row on ledstrip
            row_num+= 1
            #if at the 3rd pin/row, go back to first row, go to next column
            if (j + 1) % 3 == 0:
                row_num = 0 
                col_num += 1
    #show led 
    #led_strip.pixels_show()
    
    ledstr = ''
    for index in range(256):
        ledstr += r1[index]
        if (index+1) % ROW_STEP == 0:
            ledstr += '\n'
        elif (index+1) % 2 == 0:
            ledstr+=" "
    print(ledstr)
def LEDstrip_clear():
    for i in range(256):
        r1[i] = text_repl[0]
def prep_braille_to_segments(patterns, char_limit=32):
    '''
    breaks apart braille into list of patterns based on character limit
    default character limit is 32 (2 lines of 16 characters) (2 * 96) = (192 leds)
    '''
    pin_limit = char_limit * READ_STEP
    braille_segment_list = []
    braille_size = len(patterns)

    for i in range(0, braille_size, pin_limit):
        segment = patterns[i:min(i+pin_limit, braille_size)]
        braille_segment_list.append(segment)

    return braille_segment_list 

sample0 = "000001100000000001100000000001100000000001110000000001110000100000100000110000110000000001100000000001110000000001100100100000110000100100"
sample1 = "110010100010111000111000101010000000101100101111000000101110100000101100100010000000010100011100000000100110100000111001100010010000000000101110010100100100100010000000011110101010000000101100100010100010011110000000101111101010101001" 
sample2 = "000001110010100010111000111000101010000000101100101111000000101110100000101100100010000000010100011100000000000001100110100000111001100010000000100000101110100110000000010100011110000000010100011100000000101110010100100100100010000000011110101010000000101100100010100010011110000000101111101010101001000000000001010100000000011100101001111100111100101010011100100010"
braille_segments = prep_braille_to_segments(sample1)

for i in range(len(braille_segments)):
    print(len(braille_segments[i]))
    send_to_LEDstrip(braille_segments[i], len(braille_segments[i]))
    sleep(1)

