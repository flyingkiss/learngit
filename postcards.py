#! /usr/bin/env python
# coding=utf-8
# 翻牌圈，转牌圈，河牌圈判断策略
# 9:[]  8:pairs['four'] 7:pairs['three'][-1]+pairs['two'][-1]
# 6:color[F[0]] 5:connector[F[0]] 4:pairs['three'][-1]
# 3:pairs['two'][-1:-3:-1] 2:pairs['two'][-1] ??最大的对，有可能是个明对
# 1:max(cards[0][1],cards[1][1])


from execut import *


def action2(holeCard, muCard, gamp):  # count 1~3

    cards = initial(holeCard, muCard)  # 总体牌
    point = dict((x, []) for x in range(1, 14))
    color = dict((x, []) for x in range(1, 5))
    pairs = {'two': [], 'three': [], 'four': []} # 对子，三条， 四条
    connector = dict((x, 0) for x in range(1, 14))  # 顺子 至少俩张张连续牌
    # holeCard特征: flag
    flag = execut(cards, point, color, pairs, connector)
    validEs = validpair(cards)
    return category(flag, cards, point, color, pairs, connector, validEs, gamp)    

def category(flag, cards, point, color, pairs, connector, validEs, gamp):
    
    
    times = gamp.times
    jetton = gamp.players[gamp.mypid].jetton
    prebet= gamp.prebet
    
    # 玩家打法分析
    pid_set = []
    warning = [0, 0]
    if gamp.games>=20:
        for s in gamp.rec:
            if s[1] != 'fold':
                pid_set.append(s[0])
                pid = s[0]
                if gamp.players[pid].ft['VPIP'] <= 0.14 + (8 - gamp.persons)*0.02 and s[1] == 'raise':  # 特别紧的玩家进来并冲池底去了
                    if prebet >= (1/3.0) * gamp.pot:   # 这不是小牌应该诈唬的时候，及早抽身, 底池比率不足3：1
                        warning[0] == 1
        for pid in gamp.live:
            if pid not in pid_set:  # 后面如果有激进流打法的玩家，舍不得加注的牌也要趁早抽身
                if gamp.players[pid].ft['AF'] >4 :
                    warning[1] == 1


    #try:
    if flag in [9, 8]:  # 同花顺，金刚属第一阵列，有策略诱盘
        if times == 1:
            return increase(1, 0.25, gamp)   #价值加注 1/4池底
        else:
            if gamp.count < 3:
                return ccall(prebet)
            return increase(1, 0.75, gamp)  # 价值加注 3/4池底 
    
    if flag == 7:
        # 如果面上有三条的话，葫芦也不安全，有人raise很大，很有可能是金刚或葫芦，随机出牌的就没办法了
        if validEs['three'] == 1:
            # increase(1, 0.5, gamp) 防止对手诈唬我
            # 对手激进，我就大raise（防诈唬）, 对手保守， 我就小raise（防金刚）
            if times == 1:
                return increase(2, 3, gamp)  
            elif prebet >= float(jetton) / 3:
                return fold(prebet)
            else:
                return increase(1, 2, gamp)
            
        else:
            if times >1:
                return ccall(prebet)
            return increase(1, 0.5, gamp)  # 价值加注，要跟的会跟，不跟的不会跟

     # 牌情分析
    care = 0  #桌面牌花色顺子是否危险
    if validEs['flush4'] == 1 or validEs['straight4'] == 1:
        care = 2
    elif validEs['flush4'] == 1 or validEs['straight4'] == 1:
        care = 1

    if flag in [6, 5]:
        if care == 2:  # 若有同花明听牌或者顺子明听牌就非常危险,看凑的那张是不是大牌
            if times == 1:
                return increase(2, 3, gamp)
            elif prebet >= float(jetton) / 3:
                return fold(prebet)
            else:
                return increase(1, 2,  gamp)  
        return increase(1, 0.5, gamp)
    
   


    if flag == 4:
        if care >0:  # 如果公共牌有花色和顺子的规律或三条
            if warning[0] == 1:   #手分极紧的人加大注了
                return fold(prebet)
            if times == 1:
                return increase(2, 2, gamp)
            elif prebet >= float(jetton) / 3:
                return fold(prebet)
            else:
                return ccall(prebet)
            
        elif cards[0][1] != cards[1][1]:  # 如果是拿面上的明对凑的三条
            
            if times == 1:
                for i in [0, 1]:
                    if cards[i][1] != pairs['three'][-1] and cards[i][1] in [13, 12, 11]:  # 另一张是高牌                       
                        return increase(1, 2, gamp)  
                return increase(2, 2, gamp)  # 小高牌，看前面有没有人抬很高,试探一下                      
            elif prebet >= float(jetton) / 3:
                return fold(prebet)              
            else:
                if gamp.count == 1:
                    return increase(1, 2,  gamp) # 险牌，直接拉高迫使弃牌
                else:
                    return increase(1, 0.25, gamp)
                              
        else:
            if times >1:
                return ccall(prebet)
            return increase(1, 0.5, gamp)  #  # 手里的对成三条,狂加

    if flag == 3:  # 两暗对
        if care > 0 :
            if warning[0] == 1 or warning[1] == 1 or care == 2:  # 手风极紧的玩家下手狂加注了 明同花听牌 明顺子听牌呢？
                return fold(prebet)
            
            if times == 1:  # 如果公共牌有花色和顺子的规律
                return increase(2, 1, gamp)
            elif prebet >= float(jetton) / 4:
                return fold(prebet)
            else:
                return increase(1, 2,  gamp)
            
        elif validEs['one'] == 1:  # 有明对的话，有人raise很有可能是凑成三条或双对，对手有三条概率(4*p)%
            
            if warning[0] == 1:  # 手风极紧的玩家下手狂加注了
                return fold(prebet)
            if times == 1:
                return increase(2, 1, gamp)  # 试探加倍如果对手只是跟注弃注，下轮加大倍数，要global个值统计对手反应
            elif prebet >= float(jetton) / 4:
                return fold(prebet)
            else:
                return increase(1, 2,  gamp)
            
        else:
            if times >1:
                return ccall(prebet)
            return increase(1, 2, gamp)  # 先拉高池底

    if flag == 2:  # 分大小，大对可以选择适量raise，中对看对手反应少量raise，小对尽量check，跟不动就fold
        # 面上有明对，有人大幅raise，很有可能三条或者双对，不要冒进，其实我也是双对，只是有个明的
        # 顶对 两倍池底加  高对价值加注
        
        bestPairs = False
        flopCards = []
        for i in cards[2:]:
            flopCards.append(i[1])
            
        for i in [0, 1]:
            if cards[i][1] in pairs['two']:
                if cards[i][1] == max(flopCards):
                    bestPairs = True
                s = cards[i][1]
                
                
        if warning[0] == 1 or care == 2:  # 手风极紧的玩家下手狂加注了
            return fold(prebet)

        if validEs['one'] == 1 or care == 1:
            if times == 1:
                return increase(2, 1, gamp)  # 第一圈加一倍试探一下 
            elif prebet >= float(jetton) / 2:
                return fold(prebet)
            else:
                if s == 13 or bestPairs == True:  # 高对  有30%的可能
                    return increase(1, 2, gamp)  # 加大注，夜长梦多
                if s in [12, 11, 10]:  # 中对  有30%的可能
                    return increase(3, 2, gamp, 1.5)  # 概率加倍,
                if s in [9, 8, 7]:
                    return increase(3, 2, gamp, 2)
                else:
                    if warning[1] == 1:
                        return fold(prebet)
                    else:
                        return increase(4, 1, gamp)
                  
        if s == 13 or bestPairs == True:  # 高对  有30%的可能
            if times >1:
                return ccall(prebet)
            if jetton/(prebet+1.0)>= 10 and gamp.count == 0:
                return increase(1, 2, gamp)  # 加大注，夜长梦多
            elif prebet<jetton/3.0:
                return ccall(prebet)
            else:
                return fold(prebet)
        elif s in [12, 11, 10]:  # 中对  有30%的可能
            return increase(3, 2, gamp, 1.5)  # 概率加倍,
        elif s in [9, 8, 7]:
            return increase(3, 2, gamp, 2)
        else:        
            if warning[1] == 1:
                return fold(prebet)
            else:
                return increase(4, 1, gamp)

    if flag == 1:  # 有高牌AK，大家都是高牌的概率有(1/2)^n,若配以听牌或可check一下搏一搏大对或者胡牌，提升概率来算
        if warning[0] == 1 or warning[1] == 1 or care >0:
            return fold(prebet)
        if tingpai(cards, point, color, pairs, connector) == 0: # 激进和紧的用户进来就不要浪费了
            return increase(4, 1, gamp)
        else:  # 只有高牌无听牌
            return fold(prebet)  # 不加注值跟小注

    if flag == 0:  # 同时听暗同花暗顺子 若手上凑了两张酌情check，若只凑一张fold 最多跟两倍弃掉 顺听牌就好了
        if gamp.count == 3:
            return fold(prebet)
        else:
            return increase(1, 2, gamp)

    if flag == -1:  # 同时听暗同花暗顺子 若手上凑了两张酌情check，若只凑一张fold 最多跟两倍弃掉 顺听牌就好了
        if gamp.count == 3:
            return fold(prebet)
        else:
            return increase(4, 2, gamp)
        
    else:
        return fold(prebet)



def ccall(add_bet):
    if add_bet == 0:
        return 'check'  
    else:
        return 'call'


def fold(add_bet):

    if add_bet == 0:
        return 'check'
    #elif add_bet <= 40:
    #    return 'call'
    else:
        return 'fold'

def increase(n, d, gamp, p=3):  # 分为几类：无限加倍(永远不call),试探加倍(太大就回了)，概率加倍(太大就跟)，听牌加倍(没胡牌，只听牌)
    
    rec = gamp.rec
    re = []
    for i in rec:
        re.append(i[1])
    jetton = gamp.players[gamp.mypid].jetton
    pot = gamp.pot

    if n == 1:  # 池底加倍
        if d* gamp.pot > jetton /2.0:
            return ccall(gamp.prebet)
        else:
            bet = max(d* gamp.pot - gamp.prebet, 120)
            return 'raise' + ' ' + str(bet)
    if n == 2:  # 试探加倍，第二轮，只加一轮
        if gamp.minraise <= 2 * gamp.Maxblind:
            return 'raise' + ' ' + str(d * gamp.minraise)
        elif gamp.prebet >= float(jetton) / 3:  # ?
            return fold(gamp.prebet)
        else:
            return ccall(gamp.prebet)
    if n == 3:  # 加不动就跟
        if gamp.prebet > jetton/3.0:
            return fold(gamp.prebet)

        pot = max(gamp.pot, 200)
        if float(pot) / (d * gamp.minraise + gamp.prebet + 1.0) > p and gamp.times >1:  # ???? 一大对最后赢得概率有多少？？？
            return 'raise' + ' ' + str(d * gamp.minraise);
        elif float(pot) / (gamp.prebet + 1.0) > p:
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)

    if n == 4:
        if re.count('check') + re.count('fold') == len(re) and gamp.times > 1:  # 全是让牌,就加个筹码
            return 'raise' + ' ' + str(gamp.minraise)
        elif gamp.prebet <= d * gamp.Maxblind:  # 跟注不多选择跟注
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)

