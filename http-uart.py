import network
import socket
import time
from machine import UART, Pin

from machine import Pin
import uasyncio as asyncio

uart = machine.UART(0, baudrate=57600, tx=Pin(16), rx=Pin(17))
print(uart)
uart.write("v\r")
time.sleep(0.1)
rxData = bytes()
while uart.any() > 0:
    rxData += uart.read(1)

print(rxData.decode('utf-8'))

ssid = '********'
password = '********'

led = Pin("LED", Pin.OUT, value=0)


html = """<!DOCTYPE html>
<html>
    <head> <title>Bekonix + Web Control</title> </head>
    <body> <h1>Bekonix + Web Control</h1>
        <p>%s</p>
        <a href="/light/on">Light On</a> |
        <a href="/light/off">Light Off</a>
    </body>
</html>
"""

wlan = network.WLAN(network.STA_IF)

def connect_to_network():
    wlan.active(True)
    wlan.config(pm = 0xa11140)  # Disable power-save mode
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        led.toggle()
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])

async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)
    led_on = request.find('/light/on')
    led_off = request.find('/light/off')
    print( 'led on = ' + str(led_on))
    print( 'led off = ' + str(led_off))

    stateis = ""
    if led_on == 6:
        print("led on")
        #led.value(1)
        stateis = "LED is ON"
        uart.write("on\r")
        time.sleep(0.1)
        print(uart.readline())
    
    if led_off == 6:
        print("led off")
        #led.value(0)
        stateis = "LED is OFF"
        uart.write("off\r")
        time.sleep(0.1)
        print(uart.readline())
        
    response = html % stateis
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    print('Connecting to Network...')
    connect_to_network()

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        led.on()
        print("heartbeat")
        await asyncio.sleep(0.25)
        led.off()
        await asyncio.sleep(0.25)
        
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
