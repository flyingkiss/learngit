#! /usr/bin/env python
# coding=utf-8

import precards
import flop_round
import turn_round
import river_round


class GAMP:
    def __init__(self):
        self.Maxblind = 40  # 大盲注数起手目 40
        self.mypid = 0
        self.players = {}  # jetton mony bet flag turn cards action
        self.count = -1  # 第几轮了
        self.times = 0  # 本轮圈数times 起始1
        self.pot = 0  # 池底筹码         

        self.pos = 0  # 我的位置(第几个叫注)   
        self.last = 0  # 有几个人，只统计活人  

        self.prebet = 0  # 跟注额
        self.minraise = self.Maxblind  # 最小加注额
        self.live = []  # 只保留参加比赛的人的pid
        self.rec = []

        self.games = 0  # 统计局数
        self.persons = 8  #

        self.preflop_bet = {}
        self.gp = False
        self.cp = False

        self.now_money = 0  # 这局开始时我的money 大小盲位把盲注加上
        self.last_money = 4000
        self.pre_AL = False
        self.post_AL = False
        self.post2_AL = False
        self.post3_AL = False
        self.success_AL = 0

        self.db = {}
        

    def getPos(self):  # 统计自己的位置，活人数
        
        self.pos = len(self.live) + 1
        for pid in self.live:
            if self.players[pid].action[self.count] == '' or self.players[pid].action[self.count] == 'blind':
                self.pos -= 1
        self.last = min(len(self.live), 8)  # 竞争对手数量

    def getMinraise(self):  # 应该是bet最多的减去第二多的 吧
        bet2 = bet1 = self.players[self.mypid].bet
        p = []
        rec = self.rec
        for s in rec:
            p.append(s[1])
        if 'raise' not in p:
            preraise = self.Maxblind
        else:
            for i in range(len(rec) - 1, -1, -1):
                if rec[i][1] == 'raise':
                    bet2 = self.players[rec[i][0]].bet
                    for j in range(i - 1, -1, -1):
                        if rec[j][1] in ['call', 'raise', 'all_in']:
                            bet1 = self.players[rec[j][0]].bet
                            break
                    break
            preraise = max(bet2 - bet1, self.Maxblind)
        self.minraise = max(self.Maxblind, preraise) #得到最小加注额

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
        
    def getPreround(self):
        if self.count == 0 and self.gp == True:  # 新的一局第一轮
            for pid in self.preflop_bet.keys():
                if self.preflop_bet[pid] < 40:
                # bet>=40 就认为是入局了，因为如果后面人都fold了我就看不到了
                # 有人raise 或call过第二圈或第二轮notify就可以看到了
                    try:
                        self.players[pid].static['pre_fold'] += 1                    
                    except:
                        pass
            for pid in self.players.keys():  # 更新VPIP
                self.players[pid].ft['VPIP'] = (self.games - self.players[pid].static['pre_fold']) / float(self.games) 
            self.gp = False
            
        if self.count <=1:  # 这样子就知道后面的人是否fold了
            for pid in self.players.keys():
                self.preflop_bet[pid] = self.players[pid].bet

    def getFt(self, pid, count):
        if count == 0:
            pid_set = []
            action_set = []
            for s in self.rec:
                if s[0] != pid:
                    pid_set.append(s[0])
                    action_set.append(s[1])
                else:
                    break

        if self.players[pid].action[count] in ['raise', 'all_in']:
                if count == 0:  # 一轮多次加注呢，PFR可能大过VPIP了
                    self.players[pid].static['pre_raise'] += 1
                    if self.players[pid].flag != '':
                        self.players[pid].AL[self.players[pid].flag] += 1
                    if action_set.count('raise')> 0:  # 翻牌前raise to raise的次数
                        self.players[pid].ft['anti_AL'] +=1
                else:
                    self.players[pid].static['post_raise'] += 1
        elif self.players[pid].action[count] == 'call':
            if count == 0:
                self.players[pid].static['pre_call'] += 1
            else:
                self.players[pid].static['post_call'] += 1
        
                
    def statics(self, round_count):
        # CB持续加注，float_CB 面对持续加注时的弃牌率  STL的次数，fold_STL 面对STL的弃牌率
        self.getPreround()
            
        for pid in self.live:  # fold的人不计算，要更新上一轮的末尾行为
            if self.cp == True and self.count > 0:
            # 新的一轮，应该把上次末尾的人处理一次, turn大的这些人
                if self.players[pid].turn >= self.players[self.mypid].turn:
                    self.getFt(pid, self.count - 1)
                else:
                    self.getFt(pid, self.count)
            else:
                self.getFt(pid, self.count)
                
        self.cp = False
                                  
        for pid in self.players.keys():
            self.players[pid].ft['PFR'] = (self.players[pid].static['pre_raise']) \
                                          / float(self.games - self.players[pid].static['pre_fold'] + 1.0)
            self.players[pid].ft['BB/100'] = self.players[pid].jetton + self.players[pid].money - 4000
            # 入场加注比
            self.players[pid].ft['pre_AF'] = self.players[pid].static['pre_raise'] / float(
                self.players[pid].static['pre_call'] + 1.0)  # pre激进度
            self.players[pid].ft['post_AF'] = self.players[pid].static['post_raise'] / float(
                self.players[pid].static['post_call'] + 1.0)  # post激进度
            

    def updateStatics(self, round_count):
        die_pid = []
        for pid in self.live:  # 上轮后面fold的玩家要去掉 count == 0的时候不要变
            if self.count > 0 and self.players[pid].action[self.count - 1] == 'fold': 
                die_pid.append(pid)
        self.live = list(set(self.live)-set(die_pid))
             
        self.getRec()
        self.statics(round_count)

        die_pid = []
        for pid in self.live:  # 本轮前面fold的玩家去掉，本轮后面fold的玩家也要去掉
            if self.players[pid].action[self.count] == 'fold':
                die_pid.append(pid)
        self.live = list(set(self.live)-set(die_pid))

    def update(self, mypid, players, count, total_pot, round_count, db):
        self.Maxblind = 40
        self.pot = total_pot
        self.mypid = mypid
        self.players = players
        self.db = db
        if self.games != round_count:  # 新的一局
            self.persons = len(self.players)
            self.live = self.players.keys() 
            self.games = round_count
            self.count = -1
            
            self.now_money = self.players[self.mypid].jetton + self.players[self.mypid].money
            if self.players[self.mypid].flag == 'small blind':
                self.now_money += 20
            elif self.players[self.mypid].flag == 'big blind':
                self.now_money +=40
            if self.pre_AL == True and self.now_money > self.last_money:
                self.success_AL +=1
            self.last_money = self.now_money
            
            self.pre_AL = False
            self.post_AL = False
            self.post2_AL = False
            self.post3_AL = False
            self.gp = True   # VPIP更新标志
            for pid in self.players.keys():
                if self.players[pid].flag != '':
                    self.players[pid].AL_pos[self.players[pid].flag] += 1
        
        if self.count != count:  # 新的一轮
            self.count = count
            self.times = 1
            self.cp = True   # 新的一轮更新上次末尾人的行为
        else:                    # 不是新的一轮，又一次询问肯定是又一圈
            self.times += 1
                        
            
        self.updateStatics(round_count)   # 统计量

        self.prebet = 0  # 需要跟注的金额
        for pid in players.keys():
            self.prebet = max(self.prebet, players[pid].bet)
        self.prebet = self.prebet - players[mypid].bet  # 跟注额

        self.getPos()
        self.getMinraise()
        
       
        temp = [] # 多圈的情况下去掉自己上次的记录          
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
        self.new_bet = [0, 0, 0, 0]
        self.flag = flag
        self.turn = turn
        self.cards = list()
        self.action = ['', '', '', '']
        self.AL = {'button':0, 'small blind':0, 'big blind':0}
        self.AL_pos = {'button':0, 'small blind':0, 'big blind':0}
        self.static = dict(
            [('pre_fold', 0), ('pre_call', 0), ('pre_raise', 0), ('bluff_pos', 0),
            ('post_call', 0), ('post_raise', 0), ('check_raise', 0)])
        self.ft = dict(
            [('VPIP', 0), ('PFR', 0), ('pre_AF', 0), ('post_AF', 0), ('anti_AL', 0),  # 比大家平均水平大很多就说明是cheat
             ('BB/100', 0)])

def action(hold_card, flop, selfid, players, act_count, total_pot, round_count, gamp, db):

    k = gamp.games
    gamp.update(selfid, players, act_count, total_pot, round_count, db)
    holeCard, muCard = getCards(hold_card, flop)
    
    '''
    fo = open('ft' + str(selfid) + '.txt', 'a')
    fo.write(str(gamp.games)+'(' + str(gamp.times) + ')' +': '+str(gamp.players[selfid].ft)+'\n')
    fo.close()
    fo = open('static' + str(selfid)+'.txt', 'a')
    fo.write(str(gamp.games)+ ': '+str(gamp.players[selfid].static)+'\n')
    fo.close()
    fo = open('_AL' + str(selfid) + '.txt', 'a')
    fo.write(str(gamp.games) + ': '+str(gamp.players[selfid].AL)+' '+ str(gamp.players[selfid].AL_pos)+'\n')
    fo.close()
    '''
    try:
        if act_count == 0:
            reply = precards.action(holeCard, gamp)
        elif act_count == 1:  # muCard[0:3]
            reply = flop_round.action(holeCard, muCard, gamp)
        elif act_count == 2:
            reply = turn_round.action(holeCard, muCard, gamp)
        elif act_count == 3:
            reply = river_round.action(holeCard, muCard, gamp)
        if reply == None:
            reply = 'fold'
    except:
        return 'fold'
    return reply

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
    players['111'].bet = 0

    players['222'] = player(2000, 4000, '', 4)
    players['222'].action[count] = 'fold'
    players['222'].turn = 4
    players['222'].bet = 0

    players['333'] = player(1920, 4000, '', 5)
    players['333'].action[count] = 'fold'
    players['333'].turn = 5
    players['333'].bet = 0
    players['444'] = player(1920, 4000, '', 6)
    players['444'].action[count] = 'fold'
    players['444'].turn = 6
    players['444'].bet = 0

    players['555'] = player(2000, 4000, '', 7)
    players['666'] = player(2000, 4000, '', 8)

    holdcard = []
    holdcard.append(porker('HEARTS', '4'))
    holdcard.append(porker('DIAMONDS', 'K'))
    flop = []

    print (action(holdcard, flop, mypid, players, 0, total_pot, 23, gamp))
    print gamp.rec


    # 上一圈后面的信息
    players['555'].bet = 200
    players['555'].jeeton = 1880
    players['555'].action[count] = 'raise'
    players['555'].turn = 7
    players['666'].bet = 0
    players['666'].jeeton = 1880
    players['666'].action[count] = 'fold'
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

    print (action(holdcard, flop, mypid, players, count, total_pot,23, gamp))

