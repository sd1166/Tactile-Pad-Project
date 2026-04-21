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

ssid = ''
password = ''

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    html = """<!DOCTYPE html>
    <html>
        <head> <title>Pico W</title> </head>
        <body> <h1>WEBSERVER THING</h1>
            <div>%s</div>
        </body>
    </html>
    """

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )
        return status[0]

def open_sock():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print('listening on', addr)

    return s

def serve_pico(connection):
    # Listen for connections
    while True:
        try:
            cl, addr = s.accept()
            print('client connected from', addr)
            request = cl.recv(1024)
            print(request)

            request = str(request)
            home = request.find('/')
            recieve_text = request.find('/send')
            
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
         
            cl.close()

        except OSError as e:
            cl.close()
            print('connection closed')


if __name__ == "__main__":
    send_toLEDboard("hello")
