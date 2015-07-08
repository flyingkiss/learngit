#! /usr/bin/env python
#coding=utf-8
#翻牌圈，转牌圈，河牌圈判断策略

def initial(holeCard,muCard):
    cards=holeCard+muCard
    return cards
def estimate(cards,point,color,pairs,connector):
    for i in range(len(cards)):
        point[cards[i][1]].append(i); #第几张牌 从0开始计算
        color[cards[i][0]].append(i); # 
    num=0;
    for i in point.keys(): #一对 两对 三条 葫芦 四条
        if len(point[i])==2:
            pairs['two'].append(i); # 次数，点数由小到大排列的
        elif len(point[i])==3:
            pairs['three'].append(i);
        elif len(point[i])==4:
            pairs['four'].append(i);

        if len(point[i])>0:    #顺子
            num=num+1;
        else:
            num=0;
        connector[i]=num;

def straightFlush(cards,connector,color):  #检测同花顺
        c,flag=flush(color); #是不是同花
        if flag==True:
            pc=dict((x,0) for x in range(1,14));
            pp=dict((x,0) for x in range(1,14));
            for i in color[c]: #同花的几张牌里有没有顺子
                pp[cards[i][1]]=pp[cards[i][1]]+1;
            num=0
            for i in range(1,14):
                if pp[i]>0:
                    num=num+1;
                else:
                    num=0;
                pc[i]=num;
            t,flag=straight(pc)
            #if flag:
                #print t,t-1,t-2,t-3,t-4
            return flag
        else:
            return False
    
def flush(color,k=5):#检测同花
    flag=False
    for i in color.keys(): 
        if len(color[i])>=k: #五张同花
            flag=True;
            return i,flag  #主程序里对cards[color[i]].sorts()，选最大的同花系列
    return -1,flag

#13 2 3 4 也是顺子(对应A,2,3,4,5)最小顺子，不过第一轮策略把小牌都扔了，不太可能出这种顺子了
def straight(connector,k=5): #检测顺子  
    flag=False
    for i in range(13,0,-1): #倒着来，选最大串子
        if connector[i]>=k: #至少五张顺子(最大的数)
            flag=True
            return i,flag
    return -1,flag
    

def pair(pairs,pam): #检测葫芦,四条，三条，两对，一对  如果有，遍历一下point就找着最大的了
    if pam=='hulu':
        if len(pairs['three'])>0 and len(pairs['two'])>0:
            #print "hulu:"+str(pairs['three'][0])*3+str(pairs['two'][0])*2;
            return True
    elif pam=='two':    
        if len(pairs[pam])==2: 
            return True
    elif pam=='four' or pam=='three':
        if len(pairs[pam])>0:
            return True
    elif pam=='one':
        if len(pairs['two'])>=1:
            return True 
    return False
#胡牌：最好的情况是已有同花顺，葫芦，金刚(可以全加)顺子，同花(赢的概率算) 可以考虑all-in或者all_in一半
#大胆加注，在翻牌圈或转牌圈可以让牌示弱，分两次或三次引诱(一次加注太多导致程序计算超过上限而弃牌)，河牌圈加大注
def hupai(cards,point,color,pairs,connector):
    o1=cards[0][1];o2=cards[1][1];#两张手牌点数
    if straightFlush(cards,connector,color):   #同花顺，组成的同华顺至少要包含一张手牌
        return 9
    
    if pair(pairs,'four'):
        if o1 in pairs['four'] or o2 in pairs['four']:
            return 8
        #else:#print '明四条'
        
    if pair(pairs,'hulu'):                     
        hulu=pairs['three']+pairs['two'];
        if o1 in hulu or o2 in hulu:
            return 7
        #else:#print '明葫芦'
        
    F=flush(color,5);  # F =[pos,flag]
    if F[1]:
        if 0 in color[F[0]] or 1 in color[F[0]]:
        #这有问题，如果有五张以上同花，要保证cards不是最小的才是暗的,由于第一轮几乎把小牌杀绝，所以这尼玛概率要多小啊
            return 6
        #else:print '明同花'
            
    F=straight(connector,5)    
    if F[1]:
        s=[F[0]-x for x in range(0,5)] #s一定是对大顺子
        if (o1 in s and len(point[o1])==1) or\
           (o2 in s and len(point[o2])==1):
            return 5
        #else:print '明顺子'
    return nicepai(cards,point,color,pairs,connector)

def nicepai(cards,point,color,pairs,connector): #对子2，两对3，三条4  等级 小单对没用
    o1=cards[0][1];o2=cards[1][1];#两张手牌点数
    if pair(pairs,'three'):   #对手可能会成大三条
        if len(point[o1])==3 or len(point[o2])==3:  #检测手里两牌是否成3条//若面上有大三条呢，那就是葫芦了
            return 4
        #else:print "明三条"
        
    if pair(pairs,'two'): 
        s=pairs['two'][-1:-3:-1]   #最大的两对，有可能有三对，最小一对就没用了
        if o1 in s or o2 in s:
            if o1 in s and o2 in s:
                #print "两对全暗"
                return 3
            #else:print "一明一暗"     
        #else:print "明两对"

    if pair(pairs,'one'):  #只有一对
        if o1 in pairs['two'] or o2 in pairs['two']: #手里成一对
            return 2
        #else:print "明一对"
            

    h=[13,12] #AK是高牌           
    if o1 in h or o2 in h:#else:print '手里一张高牌'
        #if o1 in h and o2 in h:#print '手里两张高牌'
        return 1               
    return tingpai(cards,point,color,pairs,connector)

def tingpai(cards,point,color,pairs,connector): #听牌：有4张花，4张顺有必要适当跟注

    flag1 = 0
    flag2 = 0
    #检测同花暗听牌
    F=flush(color,4);  # F =[pos,flag]
    if F[1]:
        if 0 in color[F[0]] or 1 in color[F[0]]:
            #print "同花暗听牌"
            flag1 = 1
        #else:print "同花明听牌"
    #检测顺子暗听牌        
    o1=cards[0][1];o2=cards[1][1]
    for i in range(13,4,-1): # i 13~5  A~6 最小顺按23456
        m=0;s=[];
        for j in range(i,i-5,-1):
            if len(point[j])>0:
                m=m+1
                s.append(j)
            if m>=4:
                if o1 in s  or o2 in s:#预测序列里边有手牌且点数唯一(这个肯定的，不然就有一暗对了)
                    #print '顺子暗听牌'
                    flag2 = 1
                else:
                    #print '顺子明听牌'
                    return -1
    if flag1 == 1 or flag2 == 1:
        if flag1 == 1 and flag2 == 1:
            return 0
        else:
            return -1
    return -2
    
def validpair(cards):
    muCard=cards[2:]; #只检测面牌
    point=dict((x,[]) for x in range(1,14));
    color=dict((x,[]) for x in range(1,5));
    pairs={'two':[],'three':[],'four':[]};  #对子，三条， 四条
    connector=dict((x,0) for x in range(1,14));  #顺子 至少俩张张连续牌
    estimate(muCard,point,color,pairs,connector)

    validEs={'one':0,'two':0,'three':0,'flush4':0,'flush3':0,'straight4':0,'straight3':0};
    F=flush(color,4)
    if F[1]:
        #print "明4张同花听牌" 
        validEs['flush4']=1  # 自己的同花没价值了，除非手里凑的是张高牌,顺子还好点
    F=flush(color,3)
    if F[1]:
        #print "明3张同花听牌" # 自己的同花听牌没价值了，很多人都会有
        validEs['flush3']=1


    for i in range(13,4,-1): # i 13~5  A~6 最小顺按23456
        m=0;s=[];
        for j in range(i,i-5,-1):
            if len(point[j])>0:
                m=m+1
                s.append(j)
            if m >=3:
                validEs['straight3'] = 1
            if m >=4:
                validEs['straight4'] = 1
            
    if pair(pairs,'one'):
        #print "有明对"
        validEs['one']=1
    if pair(pairs,'two'):
        #print "明两对" 
        validEs['two']=1
    if pair(pairs,'three'):
        #print "明三条"
        validEs['three']=1 # 自己的葫芦,三条危险了，别人raise的话有可能有金刚，葫芦
    return validEs

def execut(cards,point,color,pairs,connector):
    estimate(cards,point,color,pairs,connector)
    return hupai(cards,point,color,pairs,connector)

