#! /usr/bin/env python
# coding=utf-8
# 起手牌判断策略

# 起手牌概率表： 牌型：{比赛人数：概率}


def action1(holeCard, gamp):  # 需要知道手牌，竞争人数，前面玩家的反应，我的投入，总奖池，以及跟注需要多大

    flag, hole= handCards(holeCard, gamp)
    return category(flag, hole, gamp)

def getOdds(hole, n):   # 手牌能量
    point = {13: 'A', 12:'K', 11:'Q', 10:'J', 9:'T', 8:'9', 7:'8', 6:'7', 5:'6', 4:'5', 3:'4', 2:'3',
             1:'2'}
    holestr = point[hole[0]] + point[hole[1]] + hole[2]
    fo = open('preflop.txt', 'rb')
    record = fo.readlines()
    cardStrength = {}
    n = max(n, 2)
    for line in record:
        pline = line.replace('\r\n', '').split('\t')
        cardStrength[pline[0]] = float(pline[n-1])
    fo.close()
    
    cardRank = sorted(cardStrength.iteritems(), key=lambda d: d[1])
    cardRank.reverse()

    pos = 169
    for i in range(len(cardRank)):
        if holestr == cardRank[i][0]:
            pos = i + 1
            odds = cardRank[i][1]
    if pos == 169:
        odds = 0

    return pos, odds * 0.01  # 牌力怎么分

def getPos(gamp):
    pos = 0
    if gamp.last - gamp.pos >= 6:  # 前位，枪口，大牌加大注。 小牌扔
        pos = 1
    elif gamp.last - gamp.pos >= 4: # 中位
        pos = 2
    elif gamp.last - gamp.pos >= 2: # 后位， 大牌保留人口， 小牌诈唬
        pos = 3
    else:
        pos = 4                    # 大小盲位， 保护自己盲注
    return pos
        

def cardTable(gamp):
    # 1：紧 2：较紧(保持较高弃牌) 3：较松 4 很松
    # 1：凶型   2：一般  4 弱型
    # 组合 21：中VIPI 高PFR（牌前牌后都要打好，最理想） 11: 低VPIP高PFR 极紧极凶（岩石玩家不要惹）
    # 41: 松凶型（随意跟注加注型，赚取对象）   # 34 松弱型： 为了看牌而跟注
    rate = [0.15, 0.26, 0.40]
    for i in range(len(rate)):
        rate[i] += (8 - gamp.persons) * 0.01  # 松弛

    players_ft = {}
    for pid in gamp.live:
        players_ft[pid] = [0, 0, 0, 0, 0]  # VPIP VPIP/PFR AF fold_3_bet  fold_CB
        if gamp.players[pid].ft['VPIP'] <= rate[0]:
            players_ft[pid][0] = 1
        elif gamp.players[pid].ft['VPIP'] <= rate[1]:
            players_ft[pid][0] = 2
        elif gamp.players[pid].ft['VPIP'] <= rate[2]:
            players_ft[pid][0] = 3
        elif gamp.players[pid].ft['VPIP'] > rate[2]:
            players_ft[pid][0] = 4

        temp = gamp.players[pid].ft['VPIP'] / (gamp.players[pid].ft['PFR'] + 1.0)   # 入场率比加注率

        if temp >= 0.7:
            players_ft[pid][1] = 1
        elif temp > 0.5:
            players_ft[pid][1] = 2
        elif temp <= 0.5:
            players_ft[pid][1] = 3

        players_ft[pid][2] = gamp.players[pid].ft['AF']  # 1.4~4之间保持 <1.4的太保守 >4的过激进
        players_ft[pid][3] = gamp.players[pid].ft['fold_3_bet']  # 3_bet时弃牌率
        players_ft[pid][4] = gamp.players[pid].ft['fold_CB']  # 连续加注的弃牌率
        
    return players_ft
                         
def handCards(holeCard, gamp):

    if holeCard[0][0] == holeCard[1][0]:
        hole = [holeCard[0][1], holeCard[1][1], 's']
    else:
        hole = [holeCard[0][1], holeCard[1][1], 'o']    
    
    # 起手很强牌 5/169  概率(8人):
    # ---29% 已有高对
    nice = [[13, 13, 'o'], [12, 12, 'o'], [11, 11, 'o'], [13, 12, 's']]
    # all_in  无限轮加对手妥协留两三个对手为止，位置靠前加大注，靠后判断persons加小注

    # 强牌 7/169
    # --21%  至少保证有个大的对，不会空手
    good = [[13, 12, 'o'], [10, 10, 'o'], [9, 9, 'o'], [8, 8, 'o'], [13, 11, 's'], [13, 11, 'o'], [13, 10, 's']]  # 中等对子和高牌

    # 中牌 13h9+ 12h11  5/169
    # --19% 凑高对且高牌有优势
    normal = [[13, 10, 'o'], [13, 9, 's'], [13, 9, 'o'], [12, 11, 's'], [12, 11, 'o']]  # raise一次即可尽量收手

    # 强投机牌 11-77   13/169 #  后面有激进玩家，pos靠后，且前面至少俩人跟进
    # 大连牌 同花连张或隔张
    # ---17%                  
    largeS = [[12, 10, 's'], [12, 9, 's'], [11, 10, 's'], [11, 9, 's'], [10, 9, 's'], [9, 8, 's']]

    # 小口袋对子：                                                                        以上是 17%的牌 很紧的选手
    smallPair = [[1, 1, 'o'], [2, 2, 'o'], [3, 3, 'o'], [4, 4, 'o'], [5, 5, 'o'], [6, 6, 'o'], [7, 7, 'o']]

    chance = largeS + smallPair

    # 混合牌 A带小同花踢脚  能凑高对高牌无优势 两张高牌 15/169 \有A也不弃牌吧。。除非加很高不然要看一下   26% 较紧的选手
    # ---17%  不要在前面少于三个人跟进者时跟进（persons>5的时候）    诈唬牌
    mix = [[13, 8, 's'], [13, 7, 's'], [13, 6, 's'], [13, 5, 's'], [13, 4, 's'], [13, 3, 's'], [13, 2, 's'],
           [13, 1, 's'], [12, 10, 'o'], [12, 9, 'o'], [11, 10, 'o'], [11, 9, 'o'], [12, 8, 's'], [8, 7, 's'], [7, 6, 's']]

    # 机会牌人少的时候才考虑 gamp.persons = 5,4,3,2 策略调整为宽松型 人多时的诈唬选择牌，特殊位置(cutoff, button, SB)
    # 机会牌1  17张 高牌或隔张高牌          带A小踢脚不同花   36% 较松的选手
    high1 = [[13, 8, 'o'], [13, 7, 'o'], [13, 6, 'o'], [13, 5, 'o'], [13, 4, 'o'], [13, 3, 'o'], [13, 2, 'o'], [13, 1, 'o'],
             [12, 7, 's'], [12, 6, 's'], [12, 5, 's'], [12, 4, 's'], [12, 3, 's']]
             

    # 机会拍2 10张     42%很松的选手
    high2 = [[11, 8, 's'], [12, 8, 'o'], [12, 7, 'o'], [12, 6, 'o'], [11, 8, 's'], [11, 7, 's'], [11, 6, 's'], [11, 5, 's'],
             [5, 4, 's'], [6, 5, 's'], [9, 7, 's'], [10, 8, 's']]

    # 牌力应该是和比赛人数， 对手风格有关系的，所以要先判断牌桌环境，在给手牌分级才合理


    # 其余弃牌
    if hole in nice:
        return 1, hole
    elif hole in good:
        return 2, hole
    elif hole in normal:
        return 3, hole
    elif hole in chance:
        return 4, hole   
    elif hole in mix:
        return 5, hole
    elif hole in high1:
        return 6, hole
    elif hole in high2:
        return 7, hole
    return 0, hole

def category(flag, hole, gamp):

    # 别人激进时保守，
    ft = cardTable(gamp)
    num = 0
    active = 0
    for pid in gamp.live:
        if pid != gamp.mypid:
            if ft[pid][1] >= ft[gamp.mypid][1]:
                num +=1
    if 2 * num > len(gamp.live) -1: # 多半激进
        active = 0.3 + (8 - gamp.persons)*0.015
    else:
        active = 0.4 + (8 - gamp.persons)*0.015

    if gamp.players[gamp.mypid].jetton >= 6000 or ft[gamp.mypid][0] >= 0.4 + (8 - gamp.persons)*0.015: # VPIP
        active = 0.26
    if gamp.persons == 2 or gamp.players[gamp.mypid].jetton <= 500 or ft[gamp.mypid][0] <= 0.26:
        active = 0.45
    
    if gamp.times == 1:
        if gamp.games <= 30 :
            return pre_cate(flag, hole, gamp)        
        else:
            return post_cate(flag, ft, hole, active, gamp)
           
    else:  # times=2 有人加注
        if gamp.games <= 30 or active == 0:                
            return again_pre_cate(flag, gamp)
        else:
            return again_post_cate(flag, ft, active, gamp)
    
        # 前面玩家的数目：n,行为：fold , check  ,call , raise , fail #第一轮只要第一圈大盲注能让牌，没响应的算做出局


def ccall(add_bet):
    if add_bet == 0:
        return 'check'
    else:
        return 'call'

def fold(add_bet):
    if add_bet == 0:
        return 'check'
    else:
        return 'fold'

def pot_odds(p, m, gamp):  # 算奖池概率
    last = gamp.persons - 1  # 还剩多少竞争对手
    minraise = gamp.minraise  # 最小加注额
    prebet = max(gamp.prebet, 40)  # 跟注额
    pot = max(gamp.pot, 100)
    alpha = 1 - 0.07*(8-gamp.persons)  # 人缺少越激进
    return float(pot) / (m * minraise + prebet) > alpha * (1 - pow(p, last)) / pow(p, last)


def increase(n, gamp, p=1):
    jetton = gamp.players[gamp.mypid].jetton

    if n == 1:  # 激进加注   池底翻倍 池底不大时使用
        if gamp.pot <= float(jetton) / 3:   # 筹码少时应该更激进才对？？
            return 'raise' + ' ' + str(gamp.pot - gamp.prebet)
        else:
            n = 5

    if n == 2:  # 给对手 2:1的池底成败率,给后面每个人加个盲
        if gamp.pot <= float(jetton) / 3:
            return 'raise' + ' ' + str(4 * gamp.Maxblind + (gamp.last - gamp.pos) * gamp.Maxblind)
        else:
            n = 5

    if n == 3:  # 计算池底加倍 被动
        if gamp.prebet > jetton/2.0:
            return fold(gamp.prebet)
        if pot_odds(p, 3, gamp):  # 没有all_in的情况且prebet在控制范围内，下才加倍，
            return 'raise' + ' ' + str(3 * gamp.minraise)
        elif pot_odds(p, 0, gamp):
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)

    if n == 4:  # 反加注
        import random
        r = round(random.random()*2*gamp.minraise) 
        return 'raise' + ' ' + str(2.5 * gamp.minraise + r)

    if n == 5:  # 提升加注 做大池底 没人加注的情况下,
        return 'raise' + ' ' + str(1 * gamp.minraise)

    if n == 6:  # 连续加注 CB，咋呼加倍
        if gamp.pot > jetton/3:
            return fold(gamp.prebet)
        bet = max((2 / 3.0) * gamp.pot - gamp.prebet, 120)
        return 'raise' + ' ' + str(bet)


def pre_cate(flag, hole, gamp):
    jetton = gamp.players[gamp.mypid].jetton
    red = []
    for s in gamp.rec:
        red.append(s[1])

    at1 = red.count('call')
    at2 = red.count('raise')
    at3 = red.count('fold')
    at4 = red.count('all_in')

    living= len(gamp.live)
    for pid in gamp.live:
        if gamp.players[pid].action[gamp.count] == 'fold':
            living -=1

    pos = getPos(gamp)
    
    if flag == 0:
        return fold(gamp.prebet)

    if flag == 1:
        if at2 + at4 == 0 or pos == 1:
            if living <=3:
                return ccall(gamp.prebet)
        else:
            return increase(4, gamp)  # 小加注

    if flag == 2:
        if at2 + at4 == 0:  # 前面没人raise就raise
            return increase(3, gamp, 0.9)  # 概率加倍
        else:
            if pos == 1:
                if pot_odds(0.9, 0, gamp):  # 如果我位置靠前，且前面没人跟注，金额不大的话跟，否则扔
                    return ccall(gamp.prebet)
                else:
                    return fold(gamp.prebet)
            else:                        # 我的位置中后，加注(继续加高)不超过获胜概率，超过就选择跟注或弃牌
                return increase(2, gamp)
            
    if flag == 3:

        if at2 + at4 == 0:  # 没人加注，都是跟注或者弃牌
            if pos == 1:  # 位置靠前
                if pot_odds(0.85, 1, gamp):  # 加注不大
                    return increase(5, gamp)
            else:   # 位置中后 加
                return increase(2, gamp) #加大了去

        temp = 0
        for i in range(len(red)-1, -1, -1):
            if red[i] == 'call':
                temp += 1
            elif red[i] == 'raise' or red[i] == 'all_in':
                break

        if temp <= 1 and gamp.players[gamp.mypid].flag not in ['big blind', 'small blind']:  # 有人加倍无人跟 且不是大盲位
            if gamp.prebet <= 80 or gamp.prebet <= jetton / 50.0:  # 小加注 跟
                return ccall(gamp.prebet)
            else:
                return fold(gamp.prebet)
        else:
            if pot_odds(0.85, 0, gamp):
                return ccall(gamp.prebet)
            else:
                return fold(gamp.prebet)
                
    if flag == 4:  # 投机牌，有小对(J)能成三条或者能成串子，同花，
        if at2 + at4 == 0:
            if gamp.players[gamp.mypid].flag in ['big blind', 'small blind']:
                return ccall(gamp.prebet)
            else:
                return increase(5, gamp)  # 没人加小加注
        else:  # 如果有人加注，慎重跟注
            if at2 + at4 >= 1 and at1 == 0:  # 有人加注没人跟
                if gamp.prebet <= jetton/50.0 and living>=2: # 至少两人入池
                    return ccall(gamp.prebet)
                else:
                    return fold(gamp.prebet)  # 积累弃牌率
            elif pot_odds(0.8, 0, gamp):  # 金额不大(只有一人加注)毕竟投机牌也很难摸    4:1            
                return ccall(gamp.prebet)  # 看牌或跟注
            else:
                return fold(gamp.prebet)
            
    if flag == 5:  # 中后位置可以玩，前面位置就不要玩了
        if pos == 1: # 前位
            return fold(gamp.prebet)
        # 位置靠后可以玩一玩
        if at2 + at4 > 0:  # 有别人抬注就弃
            if gamp.prebet <= jetton / 50.0:  # 钱比较多的话也可以跟一下
                return ccall(gamp.prebet)
            else:
                return fold(gamp.prebet)
        else:
            if at3 == len(gamp.rec):  # 如果前面全弃牌
                return increase(5, gamp)  # 加小加注
            elif at1 >= 2:  # 至少两人跟才有可玩性
                if gamp.prebet <= 80 or gamp.prebet <= jetton / 50.0:
                    return ccall(gamp.prebet)
            else:
                if gamp.prebet <= jetton/50.0 and living<=3:
                    return ccall(gamp.prebet)            
                return fold(gamp.prebet)
  
    else:   # 紧
        return fold(gamp.prebet)    
  
def post_cate(flag, ft, hole, active, gamp):
    jetton = gamp.players[gamp.mypid].jetton

    warning = 0
    red = []
    p= []
    prepid = []
    for s in gamp.rec:
        red.append(s[1])
        p.append(s[0])
        if s[1] != 'fold':
            prepid.append(s[0])
        if ft[s[0]][0] == 1 and s[1] != 'fold':  # 极紧的玩家入局，要小心
            warning = 1
            if ft[s[0]][1] == 1 and s[1] in ['all_in', 'raise']:  # 岩石型玩家加注了 采取保守策略
                if gamp.prebet > 2*gamp.Maxblind:
                    warning = 2
            
    latent = [0, 0, 0]
    postpid = []
    for pid in gamp.live:
        if pid not in p and pid !=gamp.mypid:
            if ft[pid][0] > 3 and ft[pid][1] == 1:  # 松凶型选手 ，没足够好的牌不要去诈唬
                latent[0] += 1
            elif ft[pid][0] > 3 and ft[pid][1] == 3:  # 松弱型选手 吃的对象
                latent[1] += 1
            if ft[pid][2] > 4:  # 激进型选手在后面， 选择加注玩玩大于跟注的选手
                latent[2] += 1
            postpid.append(pid)

    living= len(gamp.live)
    for pid in gamp.live:
        if gamp.players[pid].action[gamp.count] == 'fold':
            living -=1

    at1 = red.count('call')
    at2 = red.count('raise')
    at3 = red.count('fold')
    at4 = red.count('all_in')

    pos = getPos(gamp)
    
    if flag == 1:
        if at2 + at4 == 0:
            if living <=3 or pos == 1:
                return ccall(gamp.prebet)
        else:
            return increase(4, gamp)  # 2.5倍加注

    if flag == 2:
        if at2 + at4 == 0:  # 前面没人raise就raise
            if warning == 1:  # 危险等级1 少加
                return increase(5, gamp)
            else:
                return increase(2, gamp)  # 池底加注
        else:
            if pos == 1:
                if pot_odds(0.9, 0, gamp):  # 如果我位置靠前，且前面没人跟注，金额不大的话跟，否则扔 1:1的池底就可以
                    return ccall(gamp.prebet)
                else:
                    return fold(gamp.prebet)
                
            else:  # 我的位置中后，加注(继续加高)不超过获胜概率，超过就选择跟注或弃牌
                if warning == 2:  # 极紧选手加倍
                    if pot_odds(0.85, 0, gamp):  # 获胜概率降级  2:1 才进场 
                        return ccall(gamp.prebet)
                    else:  # 及时撤离
                        return fold(gamp.prebet)
                else:  # 没有岩石型玩家加倍
                    return increase(3, gamp, 0.9)  # 概率加倍,安全

    if flag == 3:
        if at2 + at4 == 0:  # 没人加注，都是跟注或者弃牌
            if warning == 1:
                return increase(5, gamp)
            if pos == 1:  # 位置靠前
                if pot_odds(0.85, 0, gamp):  # 加注不大
                    return increase(5, gamp)
            else:  # 位置中后 加
                return increase(2, gamp)

        temp = 0
        for s in red:  # 同即加注后几个人跟了
            if s == 'call':
                temp += 1
            elif s == 'raise' or s == 'all_in':
                break
            
        if warning == 2:
            if pot_odds(0.8, 0, gamp):  # 获胜概率降级  4:1 才进场
                return ccall(gamp.prebet)
            else:  # 及时撤离
                return fold(gamp.prebet)

        if temp <= 1 and gamp.players[gamp.mypid].flag not in ['big blind', 'small blind']:  # 有人加倍无人跟 且不是大盲位
            if pot_odds(0.85, 0, gamp):
                return ccall(gamp.prebet)
            else:
                return fold(gamp.prebet)
        else:
            if pot_odds(0.85, 0, gamp):
                return ccall(gamp.prebet)
            elif gamp.prebet <= 120 and warning < 2:
                return increase(4, gamp)
            return fold(gamp.prebet)
        
    if gamp.players[gamp.mypid].flag == 'big blind' and gamp.prebet == 40:  # 钱比较多的话也可以跟一下
            return ccall(gamp.prebet)
        
    bluff = False
    t = 0
    for pid in prepid+postpid:
        if gamp.players[pid].jetton > jetton:
            t += 1
        elif gamp.players[pid].ft['fold_raise'] > 0.7 or gamp.players[pid].ft['AF'] < 1:
            t += 1
    if t == len(prepid+postpid):
        bluff = True
            
    if gamp.persons <= 2:
        bluff = True

    if flag == 4:  # 投机牌， 有小对(J)能成三条或者能成串子，同花，-不成三条串子机会不大,尽量损失不大的情况下进第二轮
        
        if at2 + at4 == 0:  # 便宜看牌
            if latent[0] + latent[2] == 0:  # 后面没有松凶玩家和激进玩家
                return increase(6,gamp)                   
            else:  # 有激进玩家 就不要添柴了，要不cheat他，要不弃牌
                return fold(gamp.prebet)

        else:  # 如果有人加注，慎重跟注
            if latent[0] > 0:  # 后面有激进
                return fold(gamp.prebet)

            if warning == 2:  # 岩石型加注
                if gamp.prebet <= 80 or gamp.prebet <= jetton / 50.0:  # 小加注 跟
                    return ccall(gamp.prebet)
                else:
                    return fold(gamp.prebet)
            elif pot_odds(0.8, 0, gamp):  # 金额不大(只有一人加注)毕竟投机牌也很难摸 4:1 
                return ccall(gamp.prebet)  
            elif gamp.prebet <= 80 and pos >=3: # 后位bluff
                return increase(4, gamp)
            else:
                return fold(gamp.prebet)


    if flag == 5:  # eturn bluff(hole, 6, gamp)中后位置可以玩，前面位置就不要玩了

        if pos == 1:
            return fold(gamp.prebet)
        # 位置靠后可以玩一玩
        if at2 + at4 > 0:  # 有别人抬注就弃
            if gamp.prebet <= jetton / 50:
                return increase(6, gamp)
            else:
                return fold(gamp.prebet)
        else:  # 没人加注     
            if at3 == len(gamp.rec):  # 如果前面全弃牌
                return increase(6, gamp)  # 诈唬加倍

            if latent[0] + latent[2] == 0:  # 后面无激进玩家，要么先他诈唬，要么弃牌
                if pos > 2 and bluff == True:                    
                    return increase(4, gamp)  # 诈唬加倍
                elif gamp.prebet <= jetton / 50:
                    return ccall(gamp.prebet)
            return fold(gamp.prebet)
        

    if flag == 6 or flag == 7:  # 有发展可诈唬
        if pos == 1:
            return fold(gamp.prebet)

        if warning > 0:
            return fold(gamp.prebet)

        if at2 + at4 > 0:
            return fold(gamp.prebet)
        
        else:  # 没人加注     
            if at3 == len(gamp.rec):  # 如果前面全弃牌
                return increase(6, gamp)  # 加倍

            if latent[0] + latent[2] == 0:  # 后面无激进玩家，要么先他诈唬，要么弃牌
                if pos > 2 and bluff == True:
                    return increase(4, gamp)  # 诈唬加倍
                elif gamp.prebet <= jetton / 50:
                    return ccall(gamp.prebet)
            return fold(gamp.prebet)

    else:
        rank, odds = getOdds(hole, gamp.persons)
        if warning > 0 or living > 5 or latent[0] + latent[2] > 0 or gamp.prebet > jetton/50.0:
            return fold(gamp.prebet)
        elif float(rank/169) <= active and pos >2 and bluff == True: # 场上都是弱鱼且牌力较好，后位    
            return increase(4, gamp)
        else:
            return fold(gamp.prebet)
    
        

def again_post_cate(flag, ft, active, gamp):  # 考虑反加倍，连续加倍对手的弃牌率只在1,2,3时，4,5考虑诈唬加倍根据对手防炸能力不同

    warning = 0
    red = []
    p = []
    raise_pid = []
    for s in gamp.rec:
        red.append(s[1])
        p.append(s[0])
        if ft[s[0]][0] == 1 and s[1] != 'fold':  # 极紧的玩家入局，要小心
            warning = 1
            if ft[s[0]][1] == 1 and s[1] in ['all_in', 'raise']:  # 岩石型玩家加注了 采取保守策略
                warning = 2
        if s[1] == 'raise':
            raise_pid.append(s[0])
            
    easy = 0  # 判断诈骗犯

    for pid in raise_pid:
        if ft[pid][0] >=3 and ft[pid][1] == 1:  # 松凶型加注，好牌不要怕
            easy += 1
    if easy == len(raise_pid):
        easy = 1
    
    temp = 0
    for s in gamp.rec:
        if s[1] != 'fold' and (ft[s[0]][3] >= 0.9 or ft[s[0]][4] >= 0.9) and ft[s[0]][0] >=2:  # 松型三倍弃 选手 
            temp +=1

    living= len(gamp.live)
    for pid in gamp.live:
        if gamp.players[pid].action[gamp.count] == 'fold':
            living -=1
                
    if flag == 1:
        return ccall(gamp.prebet)
        
    if warning == 2:
        return fold(gamp.prebet)
    
    elif flag == 2 or flag == 3:
        
        if easy == 1 and warning == 0:
            return ccall(gamp.prebet)         
        if living - temp <2 and living <3 :  # 活人少于3的时候才诈唬
            return increase(6, gamp)    # CB 继续诈唬 不要同时咋呼很多人 
        else:                      
            return again_pre_cate(flag, gamp)
        
    elif flag == 4:
                
        if living - temp <2 and len(gamp.live) <3 :  # 活人少于3的时候才诈唬
            return increase(6, gamp)    # CB 继续诈唬 不要同时咋呼很多人 
        else:        
            return again_pre_cate(flag, gamp)
    
    elif warning == 1:
        return fold(gamp.prebet)
    
    else:
        return again_pre_cate(flag, gamp)

    
def again_pre_cate(flag, gamp):
    
    if flag == 0:
        return fold(gamp.prebet)
    if flag == 1:
        return ccall(gamp.prebet)  # 连续加倍
    if flag == 2:
        if pot_odds(0.9, 0, gamp):  # 1.12  # 牌在1前面10%，输赢比： 1-0.9^k      
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)       
    if flag == 3:
        if pot_odds(0.85, 0, gamp):  # 2.15  # 20:1,  我的牌比80%的牌好，输赢比：(1-0.8^k):0.8^k
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)      
    if flag == 4:
        if pot_odds(0.8, 0, gamp):  # 4 20:1,  我的牌比80%的牌好，输赢比：(1-0.8^k):0.8^k
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)
    else:
        return fold(gamp.prebet)
                
    
    
        

    



