#! /usr/bin/env python
from  action import *

__author__ = 'xiaozhao'
flop = list()
hold_card = list()
players = dict()
total_pot = 0
gamp = GAMP()
cp = True


def unpack(msg, note):
    l = msg.split('\n')
    flag = True
    while flag:
        flag = False
        for n in range(1, len(l) - 1):
            if '/' in l[n] and l[0][0:-2] == l[n][1:-1]:
                flag = True
                note.append(l[0:n + 1])
                for i in range(n + 1):
                    l.pop(0)
                break
    msg = '\n'.join(l)
    return msg


def analyse_msg(msg, s, selfid):
    global act_count
    if msg[0] == 'seat/ ':
        seat_info_msg(msg[1:-1])
    elif msg[0] == 'hold/ ':
        hold_cards_msg(msg[1:-1])
    elif msg[0] == 'inquire/ ':
        inquire_msg(msg[1:-1], s, selfid)
    elif msg[0] == 'flop/ ':
        flop_msg(msg[1:-1])
    elif msg[0] == 'turn/ ' or msg[0] == 'river/ ':
        turn_river_msg(msg[1])
    else:
        pass


def reg_msg(sc, pid, pname='xiaozhao'):
    sc.sendall('reg: %s %s \n' % (pid, pname))


def seat_info_msg(msg):
    global players
    global hold_card
    global flop
    hold_card = []
    flop = []
    players = {}
    k = 1
    for line in msg:
        flag = ''
        line = line.strip()
        if ':' in line:
            line = line.split(':')
            flag = line[0]
            line = line[1]
        l = line.strip().split(' ')
        if flag == 'button':
            players[l[0]] = player(int(l[1]), int(l[2]), flag, 8)
        else:
            players[l[0]] = player(int(l[1]), int(l[2]), flag, k)
            k += 1


def hold_cards_msg(msg):
    for line in msg:
        line = line.split(' ')
        hold_card.append(porker(line[0], line[1]))


def inquire_msg(msg, s, selfid):
    global total_pot
    act_count = 0 if len(flop) == 0 else len(flop) - 2
    global cp
    for line in msg:
        if ':' not in line:
            line = line.strip().split(' ')
            pid = line[0]
            players[pid].jetton = int(line[1])
            players[pid].money = int(line[2])
            players[pid].bet = int(line[3])
            if players[pid].turn >= players[selfid].turn and act_count > 0 and cp:
                players[pid].action[act_count - 1] = line[4]
            else:
                players[pid].action[act_count] = line[4]
        else:
            l = line.strip().split(' ')
            total_pot = int(l[2])
    cp = False

    f = open(selfid + 'playermsg', 'a')
    for pk in hold_card:
        f.write('hold_card ' + pk.color + '  ' + pk.point + '\n')
        f.write('\n')
    for pk in flop:
        f.write('flop ' + pk.color + '  ' + pk.point + '\n')
        f.write('\n*_*\n')
    for pl in players.keys():
        f.write('players: ' + pl + '  jetton:' + str(players[pl].jetton) + ' money ' + str(
            players[pl].money) + '  bet:' + str(players[pl].bet) + '  flag: ' + players[pl].flag + '  turn:' + str(
            players[pl].turn) + '   ' + '\n    ')
        for kk in players[pl].cards:
            f.write('        card:: ' + kk.color + ' : ' + kk.point + '\n        ')
        for ac in range(4):
            f.write(str(ac) + ': ' + players[pl].action[ac] + '   ')
        f.write('\n*_*\n')
    f.close()
#    s.sendall('raise 41 \n')
    send = action(hold_card, flop, selfid, players, act_count, total_pot, gamp)
    s.sendall(send + ' \n')



# s.sendall('raise 10 \n')


def flop_msg(msg):
    global cp
    cp = True
    for i in range(3):
        line = msg[i].split(' ')
        flop.append(porker(line[0], line[1]))


def turn_river_msg(msg):
    global cp
    cp = True
    msg = msg.split(' ')
    flop.append(porker(msg[0], msg[1]))


def game_over_msg(sc):
    global cp
    cp = True
    sc.close()
    exit()
