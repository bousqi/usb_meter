#!/bin/env python3

import sys
import time
import click
import serial

from struct import unpack

if sys.platform == 'win32':
    from colorama import init
    init()

def parse_packet(packet):
    data = unpack('>'+'H'*(len(packet)//2),packet)
    p_vcc  = (float)(data[1]/100)
    p_cur  = data[2]
    p_temp = data[5]
    p_cap  = data[9]
    p_ene  = (float)(data[11]/1000)
    p_dp   = (float)(data[48]/100)
    p_dm   = (float)(data[49]/100)
    p_res  = (float)(data[62]/10)

    packet_val = {}
    packet_val["Vcc"] = p_vcc
    packet_val["Cur"] = p_cur
    packet_val["T°"]  = p_temp
    packet_val["Cap"] = p_cap
    packet_val["Ene"] = p_ene
    packet_val["D+"]  = p_dp
    packet_val["D-"]  = p_dm
    packet_val["Res"] = p_res

    # data_text = ''.join(['0x%02X ' % i for i in data])
    # print (data_text)

    return packet_val


@click.command()
@click.option('--port', '-p', required=True,
              help="COM Port to connect to USB Tester")
@click.option('--baudrate', '-b',
              default=9600,
              help="Baudrate speed")
@click.option('--refresh', '-r',
              default=1000,
              help="Refresh speed in ms")
@click.option('--details', '-d',
              default=False, is_flag=True,
              help="Display all meter")
def run(port, baudrate, refresh, details):
    print ("Connecting to %s at %dbps"%(port, baudrate))
    z1serial = serial.Serial(port=port, baudrate=baudrate)
    z1serial.timeout = 2  # set read timeout

    minVcc = 10
    maxVcc = 0
    minCur = 1000
    maxCur = 0

    print (z1serial.is_open)  # True for opened
    if z1serial.is_open:
        while True:
            z1serial.write(b'\x00')
            data = z1serial.read(130)
            # data_text = ''.join(['0x%02X ' % i for i in data])
            # print (data_text)

            state = parse_packet(data)

            maxVcc = state["Vcc"] if state["Vcc"] > maxVcc else maxVcc
            minVcc = state["Vcc"] if state["Vcc"] < minVcc else minVcc
            maxCur = state["Cur"] if state["Cur"] > maxCur else maxCur
            minCur = state["Cur"] if state["Cur"] < minCur else minCur

            print("\033[2J", end='')
            print("%s : %.2fv (v%.2f ^%.2f)"%("Vcc", state["Vcc"], minVcc, maxVcc), end='')
            print(" - ", end='')
            print("%s : %4dmA (v%4d ^%4d)"%("Cur", state["Cur"], minCur, maxCur), end='')
            if details:
                print(" / ", end='')
                print("%2d°"%(state["T°"]))
                print("[ ", end='')
                print("D+- %.2fv/%.2fv"%(state["D+"],state["D-"]), end='')
                print(" | ", end='')
                print("Res %3.1fohms"%(state["Res"]), end='')
                print(" | ", end='')
                print("Ene %.2fWh"%(state["Ene"]), end='')
                print(" | ", end='')
                print("Cap %dmAh"%(state["Cap"]), end='')
                print(" ] ", end='')
            print("", end='\r')

            # print("Vcc : %.2fv\t Cur : %4dmA"%(data_s[1]/100, data_s[2]), end='\r')

            time.sleep(refresh/1000)
    else:
        print ('z1serial not open')

run()
