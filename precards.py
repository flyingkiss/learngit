#! /usr/bin/env python
# coding=utf-8
# 起手牌判断策略

# 起手牌概率表： 牌型：{比赛人数：概率}

import random

def action(holeCard, gamp):  # 需要知道手牌，竞争人数，前面玩家的反应，我的投入，总奖池，以及跟注需要多大

    flag = handCards(holeCard, gamp)
    return category(flag, holeCard, gamp)

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

    return pos  # 牌力怎么分

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

def bluff(gamp):
    mypid =gamp.mypid
    # ??
    if gamp.prebet > 80:   # 这个要用平均bet替代
        return False
    if gamp.players[gamp.mypid].flag == '':  # 两个人时应该是button吧
        return False

    # 检查 raise-raise特别多的选手，要么是擅长抓bluff要么是在挖坑
    # 三个人时就不要考虑这么多了，挖坑也跳
    raise2 = 0
    for pid in gamp.players.keys():  # 所有人中最能抓bluff的?  极松极凶类
        if pid == gamp.mypid:
            continue
        raise2 = max(raise2, gamp.players[pid].ft['anti_AL'])
            
    if gamp.persons > 3:
        for pid in gamp.live:            
            if gamp.players[pid].ft['anti_AL'] >= raise2:
                return False
            if gamp.players[pid].ft['VPIP'] >= \
                0.40 + (8 - gamp.persons) * 0.015 and gamp.players[pid].ft['pre_AF'] >= 4:
                return False
        
    if gamp.players[pid].action[0] == 'all_in':
        return False
    if random.random()*(8.0 / gamp.persons) > 0.4:  # 人越少，筹码越少，诈唬越多
        return False

    return True

def anti_bluff(pid, gamp): # 在button，SB，BB加注频繁的玩家，多半是在诈唬，选好时机要反加注吃它
    # ， 加注有人跟注或加注时不反诈唬，不诈唬
    mypid = gamp.mypid
    if gamp.players[pid].flag == '':  # 两个人时应该是button吧？
        return False
    if gamp.players[pid].ft['VPIP'] <= (8 - gamp.persons) * 0.015:  # 特别紧或者比较弱的玩家加倍了，说明很可能有好牌
        return False
    if gamp.players[pid].ft['PFR'] <= 0.5 or gamp.players[pid].ft['pre_AF'] <= 2:  #不是很激进的人激进了 
        return False
    if gamp.players[pid].action[0] == 'all_in':   # all_in 要摊牌
        return False
    if gamp.prebet >1000:  #成本太高
        return False
    if gamp.players[pid].jetton > 1.8 * gamp.players[mypid].jetton: # 大筹码玩家炸不起
        return False
    
    threshold = gamp.players[pid].AL[gamp.players[pid].flag]/\
    (gamp.players[pid].AL_pos[gamp.players[pid].flag] + 1.0) # 不是很喜欢在诈唬位诈唬的人加注了
    if threshold <= (gamp.players[mypid].AL[gamp.players[pid].flag]/\
        (gamp.players[mypid].AL_pos[gamp.players[pid].flag] + 1.0)):
        # 比我在这个位置加注加的少 
        return False 
    return True
    
def handCards(holeCard, gamp):
    if holeCard[0][0] == holeCard[1][0]:
        hole = [holeCard[0][1], holeCard[1][1], 's']
    else:
        hole = [holeCard[0][1], holeCard[1][1], 'o']
        # 起手很强牌 5/169  概率(8人):
    # ---29% 已有高对
    nice = [[13, 13, 'o'], [12, 12, 'o'], [11, 11, 'o']]  # all_in  无限轮加对手妥协

    # 强牌 6/169
    # --21%  至少保证有个大的对，不会空手
    good = [[13, 12, 's'], [13, 12, 'o'], [10, 10, 'o'], [9, 9, 'o'], [8, 8, 'o'], [13, 11, 's'], [13, 11, 'o'], [13, 10, 's']]  # 中等对子和高牌

    # 中牌 13h9+ 12h11  5/169
    # --19% 凑高对且高牌有优势
    normal = [[13, 10, 'o'], [13, 9, 's'], [13, 9, 'o'], [12, 11, 's'], [12, 10, 's'], [12, 9, 's'], [11, 10, 's'], [12, 11, 'o']]  # raise一次即可尽量收手

    # 强投机牌 11-77   13/169 #  后面有激进玩家，pos靠后，且前面至少俩人跟进
    # 大连牌 同花连张或隔张
    # ---17%                  
    largeS = [[11, 9, 's'], [10, 9, 's'], [9, 8, 's'], [10, 8, 's'], [12, 10, 'o'], [13, 8, 's'], [12, 9, 'o']]

    # 小口袋对子：                                                                        以上是 17%的牌 很紧的选手
    smallPair = [[1, 1, 'o'], [2, 2, 'o'], [3, 3, 'o'], [4, 4, 'o'], [5, 5, 'o'], [6, 6, 'o'], [7, 7, 'o']]

    chance = largeS + smallPair

    # 混合牌 A带小同花踢脚  能凑高对高牌无优势 两张高牌 15/169 \有A也不弃牌吧。。除非加很高不然要看一下   26% 较紧的选手
    # ---17%  不要在前面少于三个人跟进者时跟进（persons>5的时候）
    mix = [[13, 7, 's'], [13, 6, 's'], [13, 5, 's'], [13, 4, 's'], [13, 3, 's'], [13, 2, 's'],
           [13, 1, 's'], [11, 10, 'o'], [11, 9, 'o'], [12, 8, 's'], [8, 7, 's'],
           [7, 6, 's'], [11, 8, 's']]

    # 机会牌人少的时候才考虑 gamp.persons = 5,4,3,2 策略调整为宽松型
    # 机会牌1  17张 高牌或隔张高牌                                       36% 较松的选手
    high1 = [[13, 8, 'o'], [13, 7, 'o'], [13, 6, 'o'], [13, 5, 'o'], [13, 4, 'o'], [13, 3, 'o'], [13, 2, 'o'], [13, 1, 'o'],
             [12, 7, 's'], [12, 6, 's'], [12, 5, 's'], [12, 4, 's'], [12, 8, 'o'], [11, 7, 's'],
             [6, 5, 's'], [9, 7, 's']]

    # 机会拍2 10张     42%很松的选手
    high2 = [[12, 7, 'o'], [12, 6, 'o'], [12, 5, 'o'], [11, 8, 's'], [12, 8, 'o'], [12, 7, 'o'],
             [11, 8, 'o'], [10, 9, 'o'], [11, 6, 's'], [11, 5, 's']]
    high3 = [[12, 4, 'o'], [12, 3, 'o'], [12, 2, 'o'], [12, 1, 'o'], [12, 3, 's'], [12, 2, 's'], [12, 1, 's'],
             [11, 7, 'o'], [11, 6, 'o'], [11 ,4, 's'], [11, 3, 's'], [11, 2, 's'], [11, 1, 's'],
             [10, 6, 's'], [10, 8, 'o']]
    
    # 人减少时牌力递增的
    # 筹码多时打稳，不要随便all_in了，一下子从前四输到了最后
    # 调节手牌范围： 激进又松的人多时， 收紧手牌； 一个是需要调节手牌范围， 一个是需要调整激进度call多我就加。call少我就fold
    ft = playersFeature(gamp)
    active = 1
    if gamp.games > 50:
        active = 0
        weaks = 0
        for pid in gamp.live:
            if ft[pid][1] >= 0.40 + (8 - gamp.persons) * 0.015 and ft[pid][2] >4 and pid != gamp.mypid: # 极松凶类
                active = 0;break
            else:
                weaks +=1
        if weaks == len(gamp.live) or gamp.persons <=3: # 活着的都不是，变鲨齿鱼
            active = 1

    # 其余弃牌
    if hole in nice:
        return 1
    if hole in good:
        return 2
    if hole in normal:
        return 3
    if hole in chance:
        return 4
    if hole in mix:
        return 5
    if active == 1:  # 别人很紧比较孬或人少时放松
        if hole in high1:
            return 6
        if hole in high2 + high3:
            return 7
    if gamp.persons == 2:
        rank = getOdds(hole, 2)
        if (rank/169.0) <=0.40:
            return 8
    return 0


def playersFeature(gamp):
    # 1：紧 2：较紧(保持较高弃牌) 3：较松 4 很松
    # 1：凶型   2：一般  4 弱型
    # 组合 21：中VIPI 高PFR（牌前牌后都要打好，最理想） 11: 低VPIP高PFR 极紧极凶（岩石玩家不要惹）
    # 41: 松凶型（随意跟注加注型，赚取对象）   # 34 松弱型： 为了看牌而跟注
    rate = [0.16, 0.26, 0.40]
    for i in range(len(rate)):
        rate[i] += (8 - gamp.persons) * 0.015  # 松弛
    players_ft = {}
    for pid in gamp.players.keys():
        players_ft[pid] = [0, 0, 0]  # VPIP VPIP AF   连续加注应对诈唬失败还没有考虑
        if gamp.players[pid].ft['VPIP'] <= rate[0]:
            players_ft[pid][0] = 1
        elif gamp.players[pid].ft['VPIP'] <= rate[1]:
            players_ft[pid][0] = 2
        elif gamp.players[pid].ft['VPIP'] <= rate[2]:
            players_ft[pid][0] = 3
        elif gamp.players[pid].ft['VPIP'] > rate[2]:
            players_ft[pid][0] = 4

        if gamp.players[pid].ft['PFR'] >= 0.7:
            players_ft[pid][1] = 1
        elif gamp.players[pid].ft['PFR'] > 0.5:
            players_ft[pid][1] = 2
        elif gamp.players[pid].ft['PFR'] <= 0.5:
            players_ft[pid][1] = 3
            
        players_ft[pid][2] = gamp.players[pid].ft['pre_AF']  # 1.4~4之间保持 <1.4的太保守 >4的过激进
        
    return players_ft


def category(flag, holeCard, gamp):
    
    if len(gamp.live) == 1:
        return 'check'
    ft = playersFeature(gamp)

    if gamp.times == 1:
        return cate(flag, ft, holeCard, gamp)

    else:  # times=2 有人加注
        return again_cate(flag, ft, holeCard, gamp)

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
    alpha = 1 - 0.07 * (8 - gamp.persons)  # 人缺少越激进
    return float(pot) / (m * minraise + prebet) > alpha * (1 - pow(p, last)) / pow(p, last)


def increase(n, gamp, p=1):
    jetton = gamp.players[gamp.mypid].jetton
    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton
    if n == 1:  # 激进加注   池底翻倍 池底不大时使用
        if gamp.pot <= float(jetton) / 3:   # 筹码少时应该更激进才对？？
            return 'raise' + ' ' + str(gamp.pot - gamp.prebet)
        else:
            n = 5

    if n == 2:  # 给对手 2:1的池底成败率,给后面每个人加个盲
        if gamp.pot <= float(jetton) / 3:
            return 'raise' + ' ' + str(4 * gamp.Maxblind + int(random.random()*(gamp.last
                                    - gamp.pos) * gamp.Maxblind))
        else:
            n = 5

    if n == 3:  # 计算池底加倍 被动
        if gamp.prebet >= max(1000, jetton/3.0):
            return fold(gamp.prebet)
        if pot_odds(p, 2, gamp):  # 没有all_in的情况且prebet在控制范围内，下才加倍，
            return 'raise' + ' ' + str(2 * gamp.minraise + int(random.random()*50))
        elif pot_odds(p, 1, gamp):
            return 'raise' + ' ' + str(1 * gamp.minraise + int(random.random()*50))
        elif pot_odds(p, 0, gamp):
            return ccall(gamp.prebet)
        return fold(gamp.prebet)

    if n == 4:  # 反加注
        r = round(2.5*min(gamp.minraise, 50) + int(random.random()*150)) 
        return 'raise' + ' ' + str(r)

    if n == 5:  # 提升加注 做大池底 没人加注的情况下,
        return 'raise' + ' ' + str(1 * gamp.minraise + int(random.random()*100))

    if n == 6:  # 连续加注 CB，咋呼加倍
        bet = max((3 / 4.0) * gamp.pot - gamp.prebet, 120)
        return 'raise' + ' ' + str(bet + int(random.random()*50) )


def cate(flag, ft, holeCard, gamp):
    
    jetton = gamp.players[gamp.mypid].jetton
    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton

    warning = 0
    red = []
    p = []
    raise_pid = []  # 记录raise人的pid
    for s in gamp.rec:
        red.append(s[1])
        p.append(s[0])
        if s[1] == 'raise':
            raise_pid.append(s[0])
        if gamp.games >=50:
            if ft[s[0]][0] == 1 and s[1] != 'fold':  # 极紧的玩家入局，要小心
                warning = 1
                if ft[s[0]][1] == 1 and s[1] in ['all_in', 'raise']:  # 岩石型玩家加注了 采取保守策略
                    if gamp.prebet > 2 * gamp.Maxblind:
                        warning = 2
    latent = 0
    sign_bluff = 0
    for pid in gamp.live:
        if gamp.games >= 50:
            sign_bluff = 1
            if pid not in p and pid != gamp.mypid:
                if ft[pid][2] > 4:  # 超激进型选手在后面 pre_AF 
                    latent = 1
                    if ft[pid][0] >2 :   #不是很紧的人但是很凶的人在后面
                        sign_bluff = 0

    living = len(gamp.live)
    
    at1 = red.count('call')
    at2 = red.count('raise')
    at3 = red.count('fold')
    at4 = red.count('all_in')
    
    pos = getPos(gamp)
    
    if gamp.prebet > max(jetton/2.0, 1000, chbet(0.1, 0, gamp)):   # 如果加注这人一般不玩这么大， 突然加了这么大。。
        if holeCard[0][1] == holeCard[1][1] == 13:
            pass
        return fold(gamp.prebet)
    
    if flag == 1:
        if gamp.prebet <= 140:
            return increase(5, gamp)
        return ccall(gamp.prebet)
    
    if flag == 2:
        if gamp.prebet >= max(jetton/ 3.0, 800, chbet(0.15, 0, gamp)):   # 加条保护
            return fold(gamp.prebet)
        if at2 + at4 == 0:  # 前面没人raise就raise
            if warning == 1:  # 危险等级1 少加
                return increase(5, gamp)
            else:
                return increase(4, gamp)  # 池底加注

        else:
            if warning == 2:  # 极紧选手加倍
                if pot_odds(0.85, 0, gamp):  # 获胜概率降级  2:1 才进场
                    return ccall(gamp.prebet)
                else:  # 及时撤离
                    return fold(gamp.prebet)
            if gamp.prebet >= 200:
                return ccall(gamp.prebet)
            if pos == 1:
                if pot_odds(0.95, 0, gamp):  # 如果我位置靠前，且前面没人跟注，金额不大的话跟
                    return increase(5, gamp) # 少加点
                else:
                    return fold(gamp.prebet)
            return increase(3, gamp, 0.95)  # 概率加倍,安全

    if flag == 3:
        
        if gamp.prebet >= max(jetton/ 4.0, 660, chbet(0.20, 0, gamp)):   # 加条保护
            return fold(gamp.prebet)
        
        if at2 + at4 == 0:  # 没人加注，都是跟注或者弃牌
            if warning == 1:
                return increase(5, gamp)
            if pos == 1:  # 位置靠前
                return increase(5, gamp)
            else:  # 位置中后 加
                gamp.pre_AL = True
                return increase(4, gamp)

        if warning == 2:
            if gamp.prebet <= 80:
                return increase(5, gamp)
            if pot_odds(0.85, 0, gamp):  # 获胜概率降级  2:1 才进场
                return ccall(gamp.prebet)
            else:  # 及时撤离
                return fold(gamp.prebet)
        else:
            if gamp.prebet <= 80:
                return increase(4, gamp)
            elif pot_odds(0.9, 0, gamp):
                return ccall(gamp.prebet)
            return fold(gamp.prebet)
            
    if warning == 2 and gamp.prebet > 200:  # 极紧选手加倍
        return fold(gamp.prebet)
    
    is_bluff = bluff(gamp)
    
    if pos == 1:  # 枪口位置不要玩
        return fold(gamp.prebet)
    
    if flag == 4:  # 投机牌， 有小对(J)能成三条或者能成串子，同花，-不成三条串子机会不大,尽量损失不大的情况下进第二轮    
        if gamp.prebet > max(jetton/ 5.0, 440, chbet(0.25, 0, gamp)):   # 加条保护
            return fold(gamp.prebet)
        if at2 + at4 == 0:  # 前面没人加注
            if pos == 1 : # 枪口
                return fold(gamp.prebet)  # 没人加小加注
            elif pos == 2:
                return increase(3, gamp, 0.85)
            else:
                gamp.pre_AL = True
                return increase(4, gamp)

        else:  # 如果有人加注，慎重跟注
            if latent == 1:  # 后面有激进
                return fold(gamp.prebet)            
            if at2 + at4 >= 1 and at1 == 0 and gamp.prebet >= 200:  # 有人加注没人跟
                return fold(gamp.prebet)
            if gamp.pot <=120 and holeCard[0][1] == holeCard[1][1]:
                return increase(5, gamp)  # 看牌或跟注
            elif pot_odds(0.85, 0, gamp):  # 金额不大(只有一人加注)毕竟投机牌也很难摸 2:1
                if pos > 2:
                    return increase(5, gamp)  # 看牌或跟注
                else:
                    return ccall(gamp.prebet)
            return fold(gamp.prebet)
        
    if warning == 2:  # 极紧选手加倍
        return fold(gamp.prebet)
    
    if gamp.pos == gamp.last and gamp.prebet <= 80 and flag in [5, 6, 7, 8]: 
        return ccall(gamp.prebet)


    if flag == 5:  # 中后位置可以玩，前面位置就不要玩了
        # 位置靠后可以玩一玩
        if at2 + at4 > 0 and gamp.prebet >120:  # 有别人抬注就弃, 两个人的情况另外写
            return fold(gamp.prebet)
        
        else:  # 没人加注或加注不多
            if at3 == len(gamp.rec) and latent == 0:  # 如果前面全弃牌          
                if pos >=2:
                    gamp.pre_AL = True
                    return increase(4, gamp)
                else:
                    return fold(gamp.prebet)

            if is_bluff == True and living <=5:
                gamp.pre_AL = True
                return increase(6, gamp)  # 诈唬加倍
            if living == 2:  # 只剩一个大盲注了
                gamp.pre_AL = True
                return increase(6, gamp) 
            else:
                return fold(gamp.prebet)
            return fold(gamp.prebet)
        
    # 如果后面玩家极紧也可以扩大诈唬位置和手牌范围
    if sign_bluff == 1 and pos >1:  # 中后位
        sign_bluff = 1
    else:
        sign_bluff = 0
        
    if pos == 2 and sign_bluff == 0: # 剩下的牌前面位置不要玩
        return fold(gamp.prebet)
    if warning >= 1:
        return fold(gamp.prebet)
    
    if flag == 6 or flag == 7:  # 有发展可诈唬

        if gamp.prebet >80 or at2+ at4 > 2:      #  两个人加倍了就不要炸了那肯定大于80
            return fold(gamp.prebet)
        
        else:
            if at3 == len(gamp.rec) and latent == 0:  # 如果前面全弃牌
                gamp.pre_AL = True
                if flag == 6:
                    return increase(6, gamp)  # 诈唬加倍
                if flag == 7:
                    return increase(5, gamp)  # 诈唬加倍
                else:
                    return ccall(gamp.prebet)
            if sign_bluff == 1:
                return increase(5, gamp)      
            if is_bluff == True and living <= 5:  # 至少两人跟才有可玩性
                gamp.pre_AL = True
                return increase(6, gamp)  # 诈唬加倍,即使对手跟了，也有发展空间
            if living == 2:  # 只剩一个大盲注了
                gamp.pre_AL = True
                return increase(6, gamp)
            return fold(gamp.prebet)
            
    if flag == 8:
        if gamp.prebet >40:   
            return fold(gamp.prebet)
        if is_bluff == True and living <= 5:
            return increase(6, gamp)
        else:
            if at3 == len(gamp.rec) and latent == 0:  # 如果前面全弃牌
                gamp.pre_AL = True
                return increase(6, gamp)  # 诈唬加倍         
            if is_bluff == True and living <= 5: # 至少两人跟才有可玩性
                gamp.pre_AL = True
                return increase(6, gamp)  # 诈唬加倍,即使对手跟了，也有发展空间
            if living == 2:  # 只剩一个大盲注了
                gamp.pre_AL = True
                return increase(6, gamp) 
            return fold(gamp.prebet)
    else:
        if living == 2 and gamp.pos ==gamp.last -1 and gamp.prebet <= 80:   # 前面全弃牌,只有俩活人
            if holeCard[0][0] == holeCard[1][0]:
                hole = [holeCard[0][1], holeCard[1][1], 's']
            else:
                hole = [holeCard[0][1], holeCard[1][1], 'o']
            rank = getOdds(hole, 2)
            if (rank/169.0) <=0.40:
                return increase(6, gamp)
        return fold(gamp.prebet)
        
            
def again_cate(flag, ft, holeCard, gamp):  # 考虑反加倍，连续加倍对手的弃牌率只在1,2,3时，4,5考虑诈唬加倍根据对手防炸能力不同

    warning = 0
    red = []
    p = []
    raise_pid = []
    if gamp.games >50:
        for s in gamp.rec:
            red.append(s[1])
            p.append(s[0])
            if ft[s[0]][0] == 1 and s[1] != 'fold':  # 极紧的玩家入局，要小心
                warning = 1
                if ft[s[0]][1] == 1 and s[1] in ['all_in', 'raise']:  # 岩石型玩家加注了 采取保守策略
                    warning = 2
            if s[1] == 'raise':
                raise_pid.append(s[0])
            
    is_bluff = False
    if gamp.games >50:
        for pid in raise_pid:
            if ft[pid][0] >2 and anti_bluff(pid, gamp):
                i = p.index(pid)
                temp = True
                for j in range(i+1, len(p)):
                    if red[j] in ['raise', 'call', 'all_in']:  # 已经有人反bluff了
                        temp = False
                if temp:
                    is_bluff = True
    
    jetton = gamp.players[gamp.mypid].jetton
    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton
        
    if gamp.prebet > max(jetton/2.0, 1000):   # 如果加注这人一般不玩这么大， 突然加了这么大。。
        if holeCard[0][1] == holeCard[1][1] == 13:
            pass
        return fold(gamp.prebet)
    
    if flag == 1:   # 松的玩家可以留下来，紧的玩家踢出去
        if warning == 2:
            return ccall(gamp.prebet)
        if len(gamp.live) >3 and gamp.prebet <= 160:
            return increase(5, gamp)  # 连续加倍
        else:
            return ccall(gamp.prebet)   # 放到翻牌圈去收割
   
    if flag == 2:
        if gamp.prebet >= max(jetton/ 3.0, 850):   # 加条保护
            return fold(gamp.prebet)
        if is_bluff:
            return increase(6, gamp)  #  反bluff
        else:
            return again_pre_cate(flag, gamp)
    if warning == 2:      
        return fold(gamp.prebet)      
    if flag == 3:
        if gamp.prebet >= max(jetton/ 4.0, 660):   # 加条保护
            return fold(gamp.prebet)
        
        if is_bluff and gamp.prebet <= 600:
            return increase(5, gamp)  #  反bluff
        else:
            return again_pre_cate(flag, gamp)

    if len(gamp.live) >=3:
        if gamp.prebet > 100:
            return fold(gamp.prebet)
        else:
            return ccall(gamp.prebet)
    if gamp.prebet >= max(jetton/ 5.0, 450):   # 加条保护
        return fold(gamp.prebet)
    if flag == 4:  # 被两个人跟上了就弃掉
        if is_bluff and gamp.prebet <= 400:
            return increase(5, gamp)  #  反bluff
        else:
            return again_pre_cate(flag, gamp)

    if warning == 1:   # 极紧型还存在的话就不会有5，6,7,8
        return fold(gamp.prebet)
    else:
        return again_pre_cate(flag, gamp)


def again_pre_cate(flag, gamp):
    jetton = gamp.players[gamp.mypid].jetton
    if jetton > 5000: # 小心保前三名
        jetton = 3000
    else:
        jetton = gamp.players[gamp.mypid].jetton
    if flag == 0:
        return fold(gamp.prebet)

    if flag == 1:
        return increase(6, gamp)  # 连续加倍
    if flag == 2:
        if pot_odds(0.9, 0, gamp):  # 1.12  # 牌在1前面10%，输赢比： 1-0.9^k     
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet) #  
    if flag == 3:
        if pot_odds(0.9, 0, gamp):  # 2.15  # 20:1,  我的牌比80%的牌好，输赢比：(1-0.8^k):0.8^k
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)
    if flag == 4:
        if pot_odds(0.85, 0, gamp) and gamp.prebet <= max(500, jetton/4.0):  # 4:1,  我的牌比80%的牌好，输赢比：(1-0.8^k):0.8^k
            return ccall(gamp.prebet)
        else:
            return fold(gamp.prebet)
    elif gamp.pre_AL == True and gamp.prebet <= max(300, jetton/7.0):
        if gamp.prebet <= 100:
            return ccall(gamp.prebet)  # 不能加了。。。
    return fold(gamp.prebet)
