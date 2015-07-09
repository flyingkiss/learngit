#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'xiaozhao'
import sys
import socket
import time
from message import *


def connect(sip, sport, cip, cport):
    sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sc.bind((cip, cport))
    while sc.connect_ex((sip, sport)) != 0:
        time.sleep(0.1)
    return sc


def main():
    s = connect(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
    reg_msg(s, int(sys.argv[5]))
    note = list()
    buf = str()
    while 1:
        if len(note) < 1:
            data = buf + s.recv(1024)
            buf = unpack(data, note)
            if buf.strip() == 'game-over':
                break
        else:
            analyse_msg(note[0][:], s, sys.argv[5])
            note.pop(0)
    s.close()
