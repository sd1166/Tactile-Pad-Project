import network
import machine  
import socket
from time import sleep
import LED_board

ssid = ''
password = ''

html = """<!DOCTYPE html>
    <html>
        <head> <title>Pico W</title> </head>
        <body> <h1>WEBSERVER THING</h1>
            <div>%s</div>
        </body>
    </html>
    """
def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    

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
            
            cl.send(html)
            cl.close()

        except OSError as e:
            cl.close()
            print('connection closed')

try:
    ip = connect()
    connection = open_sock(ip)
    serve_pico(connection)
except KeyboardInterrupt:
    machine.reset()





