#! /usr/bin/env python
# coding=utf-8

# 9:[]  8:pairs['four'] 7:pairs['three'][-1]+pairs['two'][-1]
# 6:color[F[0]] 5:connector[F[0]] 4:pairs['three'][-1]
# 3:pairs['two'][-1:-3:-1] 2:pairs['two'][-1] ??最大的对，有可能是个明åﾯ?
# 1:max(cards[0][1],cards[1][1])

# river圈就要打æﾭ? pos, times, pos

import random
from execut import *


def action(holeCard, muCard, gamp):  # count 1
    cards = initial(holeCard, muCard)  # 总体çﾉ?
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
    '''
    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton
    '''
    prebet= gamp.prebet
    
    # 玩家打法分析
    pid_set = []
    warning = [0, 0]
    if gamp.games>50:
        for s in gamp.rec:
            if s[1] != 'fold':
                pid_set.append(s[0])
                pid = s[0]
                if gamp.players[pid].ft['VPIP'] <= 0.15 + (8 - gamp.persons)*0.015 and s[1] == 'raise':  # 特别紧的玩家进来并冲池底去了
                    if prebet >= (1/3.0) * gamp.pot:   # 这不是小牌应该诈唬的时候，及早抽身, 底池比率不足3ïﾼ?
                        warning[0] = 1
        for pid in gamp.live:
            if pid not in pid_set:  # 后面如果有激进流打法的玩家，舍不得加注的牌也要趁早抽èﾺ?
                if gamp.players[pid].ft['post_AF'] >3 :
                    warning[1] = 1

    flopCards = []
    for i in cards[2:]:
        flopCards.append(i[1])
        
    # flop round 诈唬策略ïﾼ? 前面玩家上轮也跟着check了，看看turn牌相比之前有无提升，比如turn出来个不同花色的小牌
    bluff = True
    for pid in gamp.live:
        if pid != gamp.mypid and gamp.players[pid].action[2] != 'check':
            bluff = False
        if gamp.players[pid].action[3] not in ['check', '']:
            bluff = False
        if gamp.players[pid].action[0] == 'all_in' or gamp.players[pid].action[1] == 'all_in':
            bluff = False
        if gamp.post2_AL == True:  # 上轮没诈唬了没成功就不要诈唬äﾺ?
            bluff = False
            
    
    if times == 1 and validEs['three'] + + validEs['flush4']+ + validEs['straight4'] + \
       validEs['flush3'] + validEs['straight3']+ validEs['one'] == 0 and bluff == True: 
        if cards[6][1] <= 7:  # 一对也算进去了
            if jetton <= 500:
                gamp.post3_AL = True
                return 'all_in'
            else: # 下重注收底池
                return increase(5, min(2*gamp.pot, 200), gamp)
            
    if flag >=2 and jetton <=300:   # 筹码少赌大的
        gamp.post_AL = True
        return 'all_in'
    
    if times >1 and gamp.post3_AL == True and flag < 2:
        return fold(gamp.prebet)
    
    
    
    if flag in [9, 8]:  # 同花顺，金刚属turn圈统统收åﾉ?
        return increase(1, 2, gamp)  

    
    if flag == 7:  # turn 圈的葫芦要杀æﾭ?
        # 如果面上有三条的话，葫芦也不安全，有人raise很大，很有可能是金刚或葫芦，随机出牌的就没办法了
        if validEs['three'] == 1:
            if gamp.prebet > max(jetton/2.0, 1000):
                return fold(gamp.prebet)
            if times == 1 and gamp.pos != gamp.last:
                return increase(5, max(2*gamp.pot, 800), gamp)
            return 'all _in'  # 有可能在钓鱼 看他check_raise的æ?ﾀ俩，不过有牌一般会加注åﾐ?
        return 'all_in' 

    
    # 牌情分析
    care = 0  #桌面牌花色顺子是否危éﾙ?
    if validEs['flush4'] == 1 or validEs['straight4'] == 1:
        care = 3
    elif validEs['flush3'] == 1 or validEs['straight3'] == 1:
        care = 2
    elif validEs['flush2'] == 1:
        care = 1
    

    if flag in [6, 5]:  # river圈的顺子ïﾼ?没有明三条才能放心加，同花只要手牌够åﾤ?
        if validEs['three'] == 1:
            if gamp.prebet >= 200:
                return fold(gamp.prebet)
            else:
                return ccall(gamp.prebet)
        if max(flopCards) < max(cards[0][1], cards[1][1]):
            return increase(5, max(1*gamp.pot, 600), gamp)
        else:
            if gamp.prebet > max(jetton/2.0, 800):
                return ccall(gamp.prebet)
            else:
                return increase(5, 80, gamp)

            
    if care == 3:   # 面上有同花听牌就该弃掉了
        if gamp.prebet > 80 and gamp.times == 1: # 小加注弃
            return fold(gamp.prebet)
        elif gamp.prebet <= 80 and gamp.times == 1: #
            return increase(4, 1, gamp)
        else:
            return fold(gamp.prebet)

        
    if flag == 4:  # turn圈的三条还是很安全的
        if care == 2:  # 如果公共牌有花色和顺子的规律或三æﾝ?
            if warning[0] == 1 and gamp.prebet > 350:   #手分极紧的人加大注了
                return fold(prebet)
            if gamp.prebet > max(jetton/2.0, 800):
                return fold(prebet)
            return increase(2, 2, gamp)
        
        if care == 1 and cards[0][1] == cards[1][1]:  # 不能让其轻易看牌
            return increase(5, max(2*gamp.pot, 300), gamp) 
        
        if cards[0][1] != cards[1][1]:  # 如果是拿面上的明对凑的三æﾝ?别人也有可能有三æﾝ?
            for i in [0, 1]:
                if cards[i][1] != pairs['three'][-1] and cards[i][1] in [13, 12]:  # 另一张是高牌                       
                    return increase(5, max(2*gamp.pot, 400), gamp)
                
            if gamp.prebet > max(jetton/2.0, 800):
                return fold(prebet)
            return increase(2, 2, gamp)
        
        # 全暗三条
        if times == 1 and gamp.prebet <=80:
            return increase(1, 2, gamp)   #价值加æﾳ?1/4池底
        else:
            return ccall(gamp.prebet)


    if flag == 3:  # 两暗åﾯ? turnåﾜ?防三æﾝ?
        if care > 0 :
            if (warning[0] == 1 or warning[1] == 1 or care == 2) and gamp.prebet >80:  # 手风极紧的玩家下手狂加注äﾺ?明同花听çﾉ?明顺子听牌呢ïﾼ?
                return fold(prebet)
            
        if gamp.prebet > max(jetton/3.0, 800):
                return fold(prebet)
        return increase(2, 2, gamp)


    if flag == 2:  # 分大小，大对可以选择适量raise，中对看对手反应少量raise，小对尽量check，跟不动就fold
        # 面上有明对，有人大幅raise，很有可能三条或者双对，不要冒进，其实我也是双对，只是有个明çﾚ?
        # 顶对 两倍池底加  高对价值加æﾳ?

        if gamp.prebet > max(jetton/3.0, 680):  # 这里应该随人数不同变åﾌ?
            return fold(gamp.prebet)
        
        bestPairs = False
        for i in [0, 1]:
            if cards[i][1] in pairs['two']:
                if cards[i][1] == max(flopCards):
                    bestPairs = True   # 判断顶对
                s = cards[i][1]                
            
        if warning[0] == 1 or care == 2 and gamp.prebet > 80:  # 手风极紧的玩家下手狂加注äﾺ?
            return fold(prebet)

        if validEs['one'] == 1 or care == 1:
            if times == 1 and gamp.prebet <= 80:
                return increase(2, 2, gamp)  # 第一圈加一倍试探一äﾸ?
            elif prebet >= 600:
                return fold(prebet)
            else:
                if gamp.prebet <= 80 :
                    if s == 13 or bestPairs == True:  # 高对  æﾜ?0%的可èﾃ?
                        return increase(3, 2, gamp, 2.5)  # 概率加åﾀ?
                    if s in [12, 11, 10]:  # 中对  æﾜ?0%的可èﾃ?
                        return increase(3, 2, gamp, 3)  # 概率加åﾀ?
                    if s in [9, 8, 7]:
                        return increase(3, 2, gamp, 4)
                    if warning[1] == 1: 
                        return fold(prebet)
                    return increase(4, 1, gamp)
                else:
                    return ccall(gamp.prebet)
                  
        if s == 13 or bestPairs == True:  # 顶对  æﾜ?0%的可èﾃ?
            return ccall(gamp.prebet)  # 加大注，夜长梦多  
        if s in [12, 11, 10]:  # 中对  æﾜ?0%的可èﾃ? 不是顶对ïﾼ?加保æﾊ?翻牌åﾜ?
            if gamp.prebet >= max(680, jetton/5.0):
                return fold(gamp.prebet)
            if gamp.pot/(gamp.prebet+1.0) >= 3:
                return increase(3, 2, gamp, 3)  # 概率加åﾀ?
            else:
                return fold(gamp.prebet)
        if s in [9, 8, 7]:
            if gamp.prebet >= max(380, jetton/6.0):
                return fold(gamp.prebet)
            if gamp.pot/(gamp.prebet+1.0) >=4:
                return increase(3, 2, gamp, 4)  # 概率加åﾀ?
            else:
                return fold(gamp.prebet)
        if warning[1] == 1 and gamp.prebet >40:
            return fold(prebet)
        else:
            if times == 1:
                if gamp.prebet >= max(120, jetton/10.0):
                    return fold(gamp.prebet)
                if gamp.pot/(gamp.prebet+1.0) >= 5:
                    return increase(4, 1, gamp)
                else:
                    return fold(gamp.prebet)
            else:
                return fold(gamp.prebet)
            

    if flag == 1:  # 有高牌A，大家都是高牌的概率æﾜ?1/2)^n,若配以听牌或可check一下搏一搏大对或者胡牌，提升概率来算
        if gamp.prebet >= 90:
            return fold(gamp.prebet)
         
        if min(cards[0][1], cards[1][1]) > 10 and gamp.pot/(gamp.prebet + 1.0) >= 6:
            if gamp.prebet == 0:
                return 'raise' + ' ' + str(44)
            else:
                return ccall(gamp.prebet)
        return fold(prebet)  # 不加注值跟小注
   
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

def increase(n, d, gamp, p=3):  # 分为几类：无限加åﾀ?永远不call),试探加åﾀ?太大就回äﾺ?，概率加åﾀ?太大就跟)，听牌加åﾀ?没胡牌，只听çﾉ?
    
    rec = gamp.rec
    re = []
    for i in rec:
        re.append(i[1])
    jetton = gamp.players[gamp.mypid].jetton
    '''
    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton
    '''
    pot = gamp.pot

    if n == 1:  # 池底加åﾀ?
        bet = max(d* gamp.pot - gamp.prebet, 120)
        return 'raise' + ' ' + str(bet)
    if n == 2:  # 试探加倍，第二轮，只加一èﾽ?
        if gamp.minraise <= 2 * gamp.Maxblind:
            return 'raise' + ' ' + str(d * gamp.minraise+ int(random.random()*50))
        elif gamp.prebet >= max(float(jetton) / 4, 400):  # ?
            return fold(gamp.prebet)
        else:
            return ccall(gamp.prebet)
    if n == 3:  # 加不动就èﾷ?
        if gamp.prebet > max(float(jetton) / 3, 600):
            return fold(gamp.prebet)
        pot = max(gamp.pot, 200)
        if float(pot) / (d * gamp.minraise + gamp.prebet + 1.0) > p:  # ???? 一大对最后赢得概率有多少？？ïﾼ?
            return 'raise' + ' ' + str(d * gamp.minraise + int(random.random()*50))
        elif float(pot) / (gamp.prebet + 1.0) > p:  # 这个p要根据对手风格调整，喜欢人大raise的人p要调小一äﾺ?
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)

    if n == 4:
        if re.count('check') + re.count('fold') == len(re) and gamp.times > 1:  # 全是让牌,就加个筹çﾠ?
            return 'raise' + ' ' + str(gamp.minraise + int(random.random()*50))
        elif gamp.prebet <= d * gamp.Maxblind:  # 跟注不多选择跟注
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)
    if n == 5:
        return 'raise' + ' ' + str(d + int(random.random()*200))

