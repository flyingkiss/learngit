#! /usr/bin/env python
from action import *

__author__ = 'xiaozhao'
flop = list()
hold_card = list()
players = dict()
total_pot = 0
gamp = GAMP()
cp = True
round_count = 0
db = dict()


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
    elif msg[0] == 'notify/ ':
        notify_msg(msg[1:-1], selfid)
    elif msg[0] == 'pot-win/ ':
        pot_win_msg(msg[1:-1])
    else:
        pass


def reg_msg(sc, pid, pname='xiaozhao'):
    sc.sendall('reg: %s %s need_notify \n' % (pid, pname))


def seat_info_msg(msg):
	global cp
    global players
    global hold_card
    global flop
    global round_count
	cp=True
    for p in players:
        players[p].bet = 0
        players[p].new_bet = [0, 0, 0, 0]
        players[p].flag = ''
    hold_card = []
    flop = []
    k = 1
    live_pid = set()
    for line in msg:
        flag = ''
        line = line.strip()
        if ':' in line:
            line = line.split(':')
            flag = line[0]
            line = line[1]
        l = line.strip().split(' ')
        live_pid.add(l[0])
        if round_count == 0:
            db[l[0]] = list()
            if flag == 'button':
                players[l[0]] = player(int(l[1]), int(l[2]), flag, 8)
            else:
                players[l[0]] = player(int(l[1]), int(l[2]), flag, k)
        else:
            players[l[0]].action = ['', '', '', '']
            players[l[0]].jetton = int(l[1])
            players[l[0]].money = int(l[2])
            players[l[0]].flag = flag
            if flag == 'button':
                players[l[0]].turn = 8
            else:
                players[l[0]].turn = k
        k += 1
    round_count += 1
    all_pid = set(players.keys())
    live_pid = all_pid - live_pid
    if len(live_pid) > 0:
        for p_id in live_pid:
            players.pop(p_id)


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
                players[pid].new_bet[act_count - 1] = int(line[3])
                players[pid].action[act_count - 1] = line[4]
            else:
                players[pid].new_bet[act_count] = int(line[3])
                players[pid].action[act_count] = line[4]
        else:
            l = line.strip().split(' ')
            total_pot = int(l[2])
    cp = False
    send = action(hold_card, flop, selfid, players, act_count, total_pot, round_count, gamp, db)
    s.sendall(send + ' \n')


def notify_msg(msg, selfid):
    global total_pot
    act_count = 0 if len(flop) == 0 else len(flop) - 2
    for line in msg:
        if ':' not in line:
            line = line.strip().split(' ')
            pid = line[0]
            players[pid].jetton = int(line[1])
            players[pid].money = int(line[2])
            players[pid].bet = int(line[3])
            if players[pid].turn >= players[selfid].turn and act_count > 0 and cp:
                players[pid].action[act_count - 1] = line[4]
                players[pid].new_bet[act_count - 1] = int(line[3])
            else:
                players[pid].action[act_count] = line[4]
                players[pid].new_bet[act_count] = int(line[3])
        else:
            l = line.strip().split(' ')
            total_pot = int(l[2])
    gamp.updateStatics(round_count)


def flop_msg(msg):
    global cp
    cp = True
    for i in range(3):
        line = msg[i].split(' ')
        flop.append(porker(line[0], line[1]))


def pot_win_msg(msg):
    for l in msg:
        ll = l.split(':')
        pid = ll[0]
        money = int(ll[1].strip())
    dump(players)



def dump(players):
    global db
    for pid in players:
        if players[pid].new_bet[0] > 0:
            db[pid].append(players[pid].new_bet[:])


def turn_river_msg(msg):
    global cp
    cp = True
    msg = msg.split(' ')
    flop.append(porker(msg[0], msg[1]))
