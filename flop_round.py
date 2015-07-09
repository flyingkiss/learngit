#! /usr/bin/env python
# coding=utf-8
# 圈river判断策略
# 9:[]  8:pairs['four'] 7:pairs['three'][-1]+pairs['two'][-1]
# 6:color[F[0]] 5:connector[F[0]] 4:pairs['three'][-1]
# 3:pairs['two'][-1:-3:-1] 2:pairs['two'][-1] ??最大的对，有可能是个明对
# 1:max(cards[0][1],cards[1][1])

# 河牌圈听牌都扔掉， 除顶对外不加了，稳赢的牌小加，不稳赢的牌为了池底
# pos, times, pos

import random
from execut import *


def action(holeCard, muCard, gamp):  # count 1
    cards = initial(holeCard, muCard)  # 总体牌
    point = dict((x, []) for x in range(1, 14))
    color = dict((x, []) for x in range(1, 5))
    pairs = {'two': [], 'three': [], 'four': []} # 对子，三条， 四条
    connector = dict((x, 0) for x in range(1, 14))  # 顺子 至少俩张张连续牌
    # holeCard特征: flag
    flag = execut(cards, point, color, pairs, connector)
    validEs = validpair(cards)
    return category(flag, cards, point, color, pairs, connector, validEs, gamp)    

def chbet(percent, count, gamp):
    Lbet = 0
    for pid in gamp.live:
        cal = []
        for s in gamp.db[pid]:
            if s[count + 1] == s[count]:
                cal.append(s[count])   # 弃牌时的bet
        if cal != [] and gamp.games < 50:
            cal.sort()
            cal.reverse()  # 由大到小
            p = cal[int(len(cal)*percent)]
            if Lbet < p:
                Lbet == p
    return Lbet

def category(flag, cards, point, color, pairs, connector, validEs, gamp):
    
    times = gamp.times
    jetton = gamp.players[gamp.mypid].jetton

    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton

    prebet= gamp.prebet
    
    # 玩家打法分析
    pid_set = []
    warning = [0, 0]
    if gamp.games > 50:
        for s in gamp.rec:
            if s[1] != 'fold':
                pid_set.append(s[0])
                pid = s[0]
                if gamp.players[pid].ft['VPIP'] <= 0.15 + (8 - gamp.persons)*0.015 and s[1] == 'raise':  # 特别紧的玩家进来并冲池底去了
                    if prebet >= (1/3.0) * gamp.pot:   # 这不是小牌应该诈唬的时候，及早抽身, 底池比率不足3：1
                        warning[0] = 1
        for pid in gamp.live:
            if pid not in pid_set:  # 后面如果有激进流打法的玩家，舍不得加注的牌也要趁早抽身
                if gamp.players[pid].ft['post_AF'] >3 :
                    warning[1] = 1
    flopCards = []
    for i in cards[2:]:
        flopCards.append(i[1])

    bluff = True
    for pid in gamp.live:
        if gamp.players[pid].action[0] == 'all_in':
            bluff = False
            
    # flop round 诈唬策略：
    
    if gamp.times == 1 and flag in [-2, -1, 0 , 1] and bluff == True:  # 牌不好才吓唬
        # 前面都check或下小注直接放大，筹码少的时候直接放大
        if flag >= 2 or flag == 0 or flag == -1:
            if jetton <= 500:
                gamp.post_AL = True
                return 'all_in'
        if gamp.pos == gamp.last and gamp.prebet <= 40: #前面都check， 也有可能是陷阱，
            gamp.post_AL = True
            return increase(5, min( 2 * gamp.pot, 100), gamp)
        
        # 牌面很干燥时，自己虽没成牌，但手牌不错，直接放大
        if validEs['three'] + validEs['flush3'] + validEs['straight3']+ validEs['one'] == 0:
            if max(flopCards) < 10 and flag != -2 and gamp.prebet <= 40:
                gamp.post_AL = True
            # 没有一张带花 但是对手可能手握一对甚至已打三条，诈唬完了是要准备跟的
                return increase(5, min(2*gamp.pot, 100), gamp)
                    
        # 牌面有顺子或同花时，可以诈唬加注，这时候玩家没成牌很容易弃牌, 一旦跟上就送了400大注.....
        if validEs['straight3']+ validEs['one'] == 0 and gamp.prebet <= 80:
            if validEs['three'] + validEs['flush3'] == 1:
                gamp.post_AL = True
                return increase(5, min(2*gamp.pot, 100), gamp)
            
    if flag >=2 and jetton <=300:   # 筹码少赌大的
        gamp.post_AL = True
        return 'all_in'
    
    if times > 1 and gamp.post_AL == True and flag <2:  # 诈唬被跟了。。的情况
        if gamp.prebet <= 80:
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)
        
    
    if flag in [9, 8]:  # 同花顺，金刚属第一阵列，有策略诱盘
        if times == 1 and gamp.prebet <=80:
            return increase(1, 0.25, gamp)   #价值加注 1/4池底
        else:
            return ccall(gamp.prebet)
 
    
    if flag == 7:  # flop 圈的葫芦基本是安全的,应该引诱一下
        # 如果面上有三条的话，葫芦也不安全，有人raise很大，很有可能是金刚或葫芦，随机出牌的就没办法了
        if validEs['three'] == 1: 
            return increase(5, max(2*gamp.pot, 800), gamp)
        else:
            if times == 1 and gamp.prebet <=80:
                return increase(1, 0.5, gamp)   #价值加注 1/4池底
            else:
                return ccall(gamp.prebet)
    
    
    care = 0  #桌面牌花色顺子是否危险
    if validEs['flush3'] == 1 or validEs['straight3'] == 1:
        care = 2
    elif validEs['flush2'] == 1 or validEs['straight2'] == 1:
        care = 1
    

    if flag in [6, 5]:  # 翻牌圈的顺子， 同花只要手牌够大，
        if max(flopCards) < max(cards[0][1], cards[1][1]):
            if times == 1 and gamp.prebet <=80:
                return increase(1, 0.5, gamp)   #价值加注 1/4池底
            else:
                return ccall(gamp.prebet)
        # 加池底赶人
        return increase(5, max(1.5*gamp.pot, 600), gamp)
        

    if flag == 4:
        if care == 2:  # 如果公共牌有花色和顺子的规律或三条
            if warning[0] == 1 and gamp.prebet > 200:   #手分极紧的人加大注了
                return fold(prebet)
            return increase(2, 2, gamp)
        
        if care == 1 and cards[0][1] == cards[1][1]:  # 不能让其轻易看牌
            return increase(5, max(2*gamp.pot, 300), gamp) 
        
        if cards[0][1] != cards[1][1]:  # 如果是拿面上的明对凑的三条 flop圈还有更大的可能性很小
            for i in [0, 1]:
                if cards[i][1] != pairs['three'][-1] and cards[i][1] in [13, 12, 11]:  # 另一张是高牌                       
                    return increase(5, max(2*gamp.pot, 400), gamp)  
            return increase(2, 2, gamp)  # 小高牌，看前面有没有人抬很高,试探一下
        # 全暗三条
        if times == 1 and gamp.prebet <= 120:
            return increase(1, 1, gamp)   #价值加注 1/4池底
        else:
            return ccall(gamp.prebet)


    if flag == 3:  # 两暗对  flop圈是绝对大牌
        if care > 0 :
            if (warning[0] == 1 or warning[1] == 1 or care == 2) and gamp.prebet >80:  # 手风极紧的玩家下手狂加注了 明同花听牌 明顺子听牌呢？
                return fold(prebet)         
            return increase(5, max(gamp.pot, 600), gamp)  # 不能让便宜看牌
        
        if times == 1 and gamp.prebet <=80:
            return increase(1, 0.5, gamp)   #价值加注 1/4池底
        else:
            return ccall(gamp.prebet)


    if flag == 2:  # 分大小，大对可以选择适量raise，中对看对手反应少量raise，小对尽量check，跟不动就fold
        # 面上有明对，有人大幅raise，很有可能三条或者双对，不要冒进，其实我也是双对，只是有个明的
        # 顶对 两倍池底加  高对价值加注       
        bestPairs = False
        for i in [0, 1]:
            if cards[i][1] in pairs['two']:
                if cards[i][1] == max(flopCards):
                    bestPairs = True   # 判断顶对
                s = cards[i][1]                
            
        if warning[0] == 1 or care == 2 and gamp.prebet >= 120:  # 手风极紧的玩家下手狂加注了
            return fold(prebet)

        if validEs['one'] == 1:  # 有对子或两张顺子同花牌？
            if prebet >= 660:
                return fold(prebet)
            if times == 1 and gamp.prebet <= 80:
                return increase(2, 2, gamp)  # 第一圈加一倍试探一下 
            else:
                if gamp.prebet <= 120:
                    if s == 13 or bestPairs == True:  # 高对  有30%的可能 也会碰到三条
                        return increase(1, 2, gamp)  # 加大注，夜长梦多
                    if s in [12, 11, 10]:  # 中对  有30%的可能
                        return increase(3, 2, gamp, 1.5)  # 概率加倍,
                    if s in [9, 8, 7]:
                        return increase(3, 2, gamp, 2)
                    if warning[1] == 1: 
                        return fold(prebet)
                    return increase(4, 1, gamp)
                else:
                    return ccall(gamp.prebet)
                  
        if s == 13 or bestPairs == True:  # 顶对  有30%的可能
            if gamp.prebet >= max(680, jetton/5.0): # 加这么大会不会对手有三条？ 阈值多大合适呢？ 我哪知道，反正输得起就合适吧
                return fold(gamp.prebet)
            if times == 1:
                return increase(5, min(2*gamp.pot, 233), gamp)  # 加大注，夜长梦多
            else:
                ccall(gamp.prebet)
        
        if s in [12, 11, 10]:  # 中对  有30%的可能, 不是顶对， 加保护 翻牌圈
            if gamp.prebet >= max(580, jetton/5.0):
                return fold(gamp.prebet)
            if gamp.pot/(gamp.prebet+1.0) >= 1.5:
                if gamp.prebet > 120:
                    return ccall(gamp.prebet)
                else:
                    return increase(3, 2, gamp, 2)  # 概率加倍,
            else:
                return fold(gamp.prebet)
        if s in [9, 8, 7]:
            if gamp.prebet >= max(480, jetton/6.0):
                return fold(gamp.prebet)
            if gamp.pot/(gamp.prebet+1.0) >= 2:
                if gamp.prebet >= 80:
                    return ccall(gamp.prebet)
                else:
                    return increase(3, 2, gamp, 2)  # 概率加倍,
                return increase(3, 2, gamp, 2)  # 概率加倍,
            else:
                return fold(gamp.prebet)
        if warning[1] == 1 and gamp.prebet >40:
            return fold(prebet)
        else:
            if times == 1:
                if gamp.prebet >= max(180, jetton/10.0):
                    return fold(gamp.prebet)
                if gamp.pot/(gamp.prebet+1.0) >= 2.5:
                    return increase(4, 1, gamp)
                else:
                    return fold(gamp.prebet)
            else:
                return fold(gamp.prebet)
            

    if flag == 1:  # 有高牌A，大家都是高牌的概率有(1/2)^n,若配以听牌或可check一下搏一搏大对或者胡牌，提升概率来算
        if gamp.prebet >= max(280, jetton/10.0):
            return fold(gamp.prebet)
        if gamp.pot/(gamp.prebet+1.0) >= 5:  # 双听牌 20%的概率还是有的
            if tingpai(cards, point, color, pairs, connector) == 0:
                if times == 1 and gamp.pos == 1:
                    return increase(5, min(4*gamp.minraise, 187), gamp)             
                return ccall(gamp.prebet)
        
         # 只有高牌无听牌 虽然没打中，但还有机会, 弃还是不弃？
         
        if min(cards[0][1], cards[1][1]) > 10 and gamp.pot/(gamp.prebet + 1.0) >= 6 and gamp.prebet < 120:
            if gamp.prebet == 0:
                return 'raise' + ' ' + str(80)
            else:
                return ccall(gamp.prebet)
        return fold(prebet)  # 不加注值跟小注

    if flag == 0:  # 同时听暗同花暗顺子 
        if times == 1 and gamp.pos == 1 and gamp.prebet <=  max(jetton/4, 600):
            return increase(5, min(4*gamp.minraise, 300), gamp)
        else:
            if gamp.prebet > max(jetton/4, 600):
                return fold(gamp.prebet)  # 太大风险底池再诱人也输不起啊
            return ccall(gamp.prebet)
    
                        
    if flag == -1:  # 听暗同或花暗顺子 若手上凑了两张酌情check，若只凑一张fold 最多跟两倍弃掉 顺听牌就好了

        if max(flopCards) < max(cards[0][1], cards[1][1]) and gamp.prebet <= 380: # 内顺子就不要了，两头顺子，且凑了俩张
            if gamp.pot/(gamp.prebet+1.0) >= 5:     
                if times == 1 and gamp.pos == 1:
                    return increase(5, min(2*gamp.minraise, 100), gamp)
                else:
                    return ccall(gamp.prebet)      
            return fold(prebet)
        return fold(prebet)
    
    else:
        if gamp.prebet <= 40:
            return ccall(gamp.prebet)
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

    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton
        
    pot = gamp.pot

    if n == 1:  # 池底加倍
        bet = max(d* gamp.pot - gamp.prebet, 120)
        return 'raise' + ' ' + str(bet)
    if n == 2:  # 试探加倍，第二轮，只加一轮
        if gamp.minraise <= 3 * gamp.Maxblind:
            return 'raise' + ' ' + str(d * gamp.minraise+ int(random.random()*50))
        elif gamp.prebet > max(float(jetton) / 4, 500):  # ?      
            return fold(gamp.prebet)
        else:
            return ccall(gamp.prebet)
    if n == 3:  # 加不动就跟
        if gamp.prebet > max(float(jetton) / 3.0, 680):
            return fold(gamp.prebet)
        pot = max(gamp.pot, 200)
        if float(pot) / (d * gamp.minraise + gamp.prebet + 1.0) > p:  # ???? 一大对最后赢得概率有多少？？？
            return 'raise' + ' ' + str(d * gamp.minraise + int(random.random()*55))
        elif float(pot) / (gamp.prebet + 1.0) > p:  # 这个p要根据对手风格调整，喜欢人大raise的人p要调小一些
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)

    if n == 4:
        if re.count('check') + re.count('fold') == len(re) and gamp.times > 1:  # 全是让牌,就加个筹码
            return 'raise' + ' ' + str(gamp.minraise + int(random.random()*50))
        elif gamp.prebet <= d * gamp.Maxblind:  # 跟注不多选择跟注
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)
    if n == 5:
        return 'raise' + ' ' + str(d + int(random.random()*200))

