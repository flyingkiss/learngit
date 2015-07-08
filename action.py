#! /usr/bin/env python
# coding=utf-8

import precards
import postcards


class GAMP:
    def __init__(self):
        self.Maxblind = 40  # 大盲注数起手目 40
        self.mypid = 0
        self.players = {}  # jetton mony bet flag turn cards action
        self.count = 0  # 第几轮了
        self.times = 0  # 本轮圈数times 起始1
        self.pot = 0  # 池底筹码         

        self.pos = 0  # 我的位置(第几个叫注)   
        self.last = 0  # 有几个人，只统计活人  

        self.prebet = 0  # 跟注额
        self.preraise = 0  # 上次加注额  
        self.minraise = max(self.Maxblind, self.preraise)  # 最小加注额
        self.live = []  # 只保留参加比赛的人的pid
        self.rec = []
        self.prerec = {}

        self.games = 0  # 统计局数
        self.persons = 8  #

    def getLive(self):
        try:
            if self.count == 0 and self.times == 1:  # action里我后面的人还边没记录
                self.live = []  # 一局清空一次
                for pid in self.players.keys():
                    if self.players[pid].jetton >= self.Maxblind:  # 筹码小于大盲注认为已本场出局
                        self.live.append(pid)
                        self.prerec[pid] = ''  # prerec 一局清空一次
                self.persons = len(self.live)  # 几人桌？

            elif self.count > 0 and self.times == 1:
                temp = []
                for pid in self.live:
                    if 'fold' != self.players[pid].action[self.count - 1]:  # 上轮的操作是fold的去掉
                        temp.append(pid)

                self.live = temp
            else:
                temp = []
                for pid in self.live:
                    if self.prerec[pid] != 'fold':  # 本轮上圈的操作是fold的去掉,self.players此时还未更新，仍是上圈记录
                        temp.append(pid)
                self.live = temp
        except:
            self.live = []  # 一局清空一次
            for pid in self.players.keys():
                if self.players[pid].jetton >= self.Maxblind:  # 筹码小于大盲注认为已本场出局
                    self.live.append(pid)

    def getPos(self):  # 统计自己的位置，活人数

        self.pos = len(self.live) + 1
        if self.times == 1:
            for pid in self.live:
                if self.players[pid].action[self.count] == '' or self.players[pid].action[self.count] == 'blind':
                    self.pos -= 1

        self.last = min(len(self.live), 8)  # 竞争对手数量

    def getPreraise(self):
        bet2 = bet1 = self.players[self.mypid].bet
        p = []
        rec = self.rec
        for s in rec:
            p.append(s[1])
        if 'raise' not in p:
            self.preraise = self.Maxblind
        else:
            for i in range(len(rec) - 1, -1, -1):
                if rec[i][1] == 'raise':
                    bet2 = self.players[rec[i][0]].bet
                    for j in range(i - 1, -1, -1):
                        if rec[j][1] in ['call', 'raise', 'all_in']:
                            bet1 = self.players[rec[j][0]].bet
                            break
                    break
            self.preraise = max(bet2 - bet1, self.Maxblind)

    def getRec(self):  # 提取rec按找出牌顺序，还有preraise即上次加注额        

        temp = {}
        for pid in self.live:
            if self.players[pid].action[self.count] not in ['', 'blind']:
                temp[pid] = self.players[pid].turn

        temp1 = sorted(temp.iteritems(), key=lambda d: d[1])  # pid按turn从小到大排序
        self.rec = []
        t1 = []
        t2 = []
        for s in temp1:
            if s[1] < self.players[self.mypid].turn:
                t1.append([s[0], self.players[s[0]].action[self.count]])
            elif s[1] >= self.players[self.mypid].turn:
                t2.append([s[0], self.players[s[0]].action[self.count]])

        self.rec = t2 + t1

    def statics(self):
        # CB持续加注，float_CB 面对持续加注时的弃牌率  STL的次数，fold_STL 面对STL的弃牌率

        if self.count == 0:
            for pid in self.players.keys():
                if self.times == 1 and self.players[pid].action[self.count] not in ['', 'blind', 'fold']:
                    self.players[pid].static['mn'] += 1
                    if self.players[pid].static['mn'] == 51:  # 统计最近50入局的平均押注额
                        self.players[pid].static['all_bet'] -= self.players[pid].ft['aver_bet']
                        self.players[pid].static['mn'] = 50
                    self.players[pid].static['all_bet'] += self.players[pid].static['pre_bet']
                    self.players[pid].ft['aver_bet'] = float(self.players[pid].static['all_bet']) / \
                                                       self.players[pid].static['mn']
                self.players[pid].static['pre_bet'] = self.players[pid].bet
        re = []
        for s in self.rec:
            re.append(s[0])
        for pid in re:
            if self.players[pid].action[self.count] == 'fold':
                if self.count == 0:  # 如果是翻牌前
                    self.players[pid].static['pre_fold'] += 1
                self.players[pid].static['all_fold'] += 1

            elif self.players[pid].action[self.count] in ['raise', 'all_in']:
                if self.count == 0:  # 一轮多次加注呢，PFR可能大过VPIP了
                    self.players[pid].static['pre_raise'] += 1
                self.players[pid].static['all_raise'] += 1
            elif self.players[pid].action[self.count] == 'call':
                self.players[pid].static['all_call'] += 1

            self.players[pid].static['all_action'] += 1

            self.players[pid].ft['VPIP'] = (self.games - self.players[pid].static['pre_fold']) / float(
                self.games)  # 入局率
            self.players[pid].ft['PFR'] = (self.players[pid].static['pre_raise']) / float(self.games)  # 翻牌前的加注率
            self.players[pid].ft['AF'] = self.players[pid].static['all_raise'] / float(
                self.players[pid].static['all_call'] + 1.0)  # 激进度
            self.players[pid].ft['BB/100'] = self.players[pid].jetton + self.players[pid].money - 6000  # 盈利

        flag = False
        for i in range(len(self.rec)):
            # 持续加注的行为
            if self.rec[i][1] in ['raise', 'all_in'] and self.prerec[self.rec[i][0]] == 'raise':  # 连两圈都是加注
                self.players[self.rec[i][0]].static['CB'] += 1  # 统计持续加注的行为
                self.players[self.rec[i][0]].ft['CB'] = self.players[self.rec[i][0]].static['CB'] / float(
                    self.players[self.rec[i][0]].static['all_action'])

                for j in range(i + 1, len(self.rec)):  # 后面人面对连续加注的行为
                    self.players[self.rec[j][0]].static['face_CB'] += 1  # 面对连续加注的次数
                    if self.rec[j][1] == 'fold':
                        self.players[self.rec[j][0]].static['fold_CB'] += 1  # 连续加注后吓退的，这也得看加注加多少啊 要加就加 2/3 ~ 3/4的pot
                        self.players[self.rec[j][0]].ft['fold_CB'] = self.players[self.rec[j][0]].static[
                                                                         'fold_CB'] / float(
                            self.players[self.rec[j][0]].static['face_CB'])  # 面对连续加注下的弃牌率
            # 反加注的行为
            if self.rec[i][1] == 'raise':
                if flag == False:
                    flag = True
                    continue
                elif flag == True:  # 反加注行为     两个玩家加注叫做反加注
                    self.players[self.rec[i][0]].static['3_bet'] += 1  # 玩家i的反加注行为
                    self.players[self.rec[i][0]].ft['3_bet'] = self.players[self.rec[i][0]].static['3_bet'] \
                                                               / float(self.players[self.rec[i][0]].static['all_action'])
                    for j in range(i + 1, len(self.rec)):
                        self.players[self.rec[j][0]].static['face_3_bet'] += 1  # 面对连续加注的次数
                        if self.rec[j][1] == 'fold':
                            self.players[self.rec[j][0]].static['fold_3_bet'] += 1  # 连续加注后吓退的，这也得看加注加多少啊 要加就加 2/3 ~ 3/4的pot
                            self.players[self.rec[j][0]].ft['fold_3_bet'] = self.players[self.rec[j][0]].static[
                                    'fold_3_bet']/float(self.players[self.rec[j][0]].static['face_3_bet'])  # 面对连续加注下的弃牌率
            if self.rec[i][1] == 'raise' and gamp.count == 0:
                for j in range(i+1, len(self.rec)):
                    self.players[self.rec[j][0]].static['face_raise'] += 1             
                    if self.rec[j][1] == 'fold':
                        self.players[self.rec[j][0]].static['fold_raise'] += 1
                        self.players[self.rec[j][0]].ft['fold_raise'] = self.players[self.rec[j][0]].static[
                                    'fold_raise']/float(self.players[self.rec[j][0]].static['face_raise'])  # 面对加注下的弃牌率
                        self.players[self.rec[j][0]].cheat.append(self.players[self.rec[i][0]].bet -
                                                                  self.players[self.rec[j][0]].bet)
                    if self.rec[j][1] == 'raise':
                        break      

    def updateStatics(self):
        self.getLive()
        self.getRec()
        self.statics()
        self.prerec = {}
        for pid in self.players.keys():
            self.prerec[pid] = self.players[pid].action[self.count]

    def update(self, mypid, players, count, total_pot):
        self.Maxblind = 40
        self.pot = total_pot
        self.mypid = mypid

        if self.count != count:  # 新的一轮
            self.count = count
            self.times = 1
        elif players[mypid].action[self.count] not in ['', 'blind']:  # 我有行为时认为是第二轮
            self.times += 1
        else:  # 我无行为或只有大盲注时认为是刚开局 count=0且上局第一轮就结束了
            self.times = 1

        if self.count == 0 and self.times == 1:  # 统计这是第几局了
            self.games += 1

        self.players = players
        
        self.updateStatics()

        self.prebet = 0  # 需要跟注的金额
        for pid in players.keys():
            self.prebet = max(self.prebet, players[pid].bet)
        self.prebet = self.prebet - players[mypid].bet  # bet一局清空一次

        self.getPos()
        self.getPreraise()
        self.minraise = max(self.Maxblind, self.preraise)

        temp = []  # 去掉自己的记录
        for s in self.rec:
            if s[0] != self.mypid:
                temp.append(s)
        self.rec = temp


class porker:
    def __init__(self, color, point):
        self.color = color
        self.point = point


class player:
    def __init__(self, jetton, money, flag, turn):
        self.jetton = jetton
        self.money = money
        self.bet = 0
        self.flag = flag
        self.turn = turn
        self.cards = list()
        self.action = ['', '', '', '']
        self.static = dict(
            [('pre_fold', 0), ('pre_call', 0), ('pre_raise', 0), ('3_bet', 0), ('fold_3_bet', 0), ('face_3_bet', 0),
             ('all_call', 0), ('all_fold', 0), ('all_raise', 0), ('all_action', 0), ('CB', 0), ('fold_CB', 0),
             ('face_raise', 0), ('fold_raise', 0), ('face_CB', 0), ('BB/100', 0), ('pre_bet', 0), ('all_bet', 0), ('mn', 0)])
        self.ft = dict(
            [('VPIP', 0), ('PFR', 0), ('AF', 0), ('3_bet', 0), ('STL', 0), ('fold_STL', 0), ('fold_3_bet', 0), \
             ('CB', 0), ('fold_CB', 0), ('BB/100', 0), ('aver_bet', 0), ('fold_raise', 0), ('call_raise', 0)])
        self.cheat = []


def action(hold_card, flop, selfid, players, act_count, total_pot, gamp):
    gamp.update(selfid, players, act_count, total_pot)
    holeCard, muCard = getCards(hold_card, flop)
    if act_count == 0:
        return precards.action1(holeCard, gamp)
    elif act_count > 0:  # muCard[0:3]
        return postcards.action2(holeCard, muCard, gamp)


def getCards(holdcard, flop):  # flop? flop顺序是个啥，新翻的牌在前在后？
    color = {'SPADES': 1, 'HEARTS': 2, 'CLUBS': 3, 'DIAMONDS': 4}
    point = {'A': 13, 'K': 12, 'Q': 11, 'J': 10, '10': 9, '9': 8, '8': 7, '7': 6, '6': 5, '5': 4, '4': 3, '3': 2,
             '2': 1}
    holeCard = []
    muCard = []
    for card in holdcard:
        holeCard.append([color[card.color], point[card.point]])
    for card in flop:
        muCard.append([color[card.color], point[card.point]])
    holeCard = sorted(holeCard, key=lambda d: d[1])
    holeCard.reverse()

    return holeCard, muCard


if __name__ == '__main__':
    import time

    start = time.time()
    gamp = GAMP()
    players = {}
    mypid = '555'
    count = 0

    total_pot = 60 + 40 + 80 + 80
    players['777'] = player(1980, 4000, '', 1)
    players['777'].action[count] = 'blind'
    players['777'].turn = 1  # samll blind
    players['777'].bet = 20

    players['888'] = player(1960, 4000, '', 2)
    players['888'].action[count] = 'blind'
    players['888'].turn = 2  # bigblind
    players['888'].bet = 40

    players['111'] = player(1960, 4000, '', 3)
    players['111'].action[count] = 'call'
    players['111'].turn = 3
    players['111'].bet = 40

    players['222'] = player(2000, 4000, '', 4)
    players['222'].action[count] = 'fold'
    players['222'].turn = 4
    players['222'].bet = 0

    players['333'] = player(1920, 4000, '', 5)
    players['333'].action[count] = 'raise'
    players['333'].turn = 5
    players['333'].bet = 80
    players['444'] = player(1920, 4000, '', 6)
    players['444'].action[count] = 'call'
    players['444'].turn = 6
    players['444'].bet = 80

    players['555'] = player(2000, 4000, '', 7)
    players['666'] = player(2000, 4000, '', 8)

    holdcard = []
    holdcard.append(porker('HEARTS', '6'))
    holdcard.append(porker('DIAMONDS', 'K'))
    flop = []

    print (action(holdcard, flop, mypid, players, count, total_pot, gamp))
    print (gamp.rec)

    # 上一圈后面的信息
    players['555'].bet = 200
    players['555'].jeeton = 1880
    players['555'].action[count] = 'raise'
    players['555'].turn = 7
    players['666'].bet = 200
    players['666'].jeeton = 1880
    players['666'].action[count] = 'call'
    players['666'].turn = 8

    players['777'].bet = 200
    players['777'].jeeton = 1880
    players['777'].action[count] = 'call'
    players['777'].turn = 1
    players['888'].bet = 200
    players['888'].jeeton = 1880
    players['888'].action[count] = 'call'
    players['888'].turn = 2
    players['111'].bet = 360
    players['111'].jeeton = 1760
    players['111'].action[count] = 'raise'
    players['111'].turn = 3
    players['222'].bet = 0
    players['222'].jeeton = 2000
    players['222'].action[count] = 'fold'
    players['222'].turn = 4
    players['333'].bet = 40
    players['333'].jeeton = 1960
    players['333'].action[count] = 'fold'
    players['333'].turn = 5
    players['444'].bet = 40
    players['444'].jeeton = 1760
    players['444'].action[count] = 'call'
    players['444'].turn = 6

    print (action(holdcard, flop, mypid, players, count, total_pot, gamp))
    print (gamp.rec)
