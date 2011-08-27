import logic
import time
import config
import confs
import utils
import logging

gCooldowns = {}
gTargets = {}

def setCooldown(who, hits):
    who = unicode(who)
    if '@' in who:
        who = utils.jidStrip(who)
    global gCooldowns
    if who in gCooldowns:
        newhits = gCooldowns[who][0]
    else:
        newhits = logic.getVitality(who)
    gCooldowns[who] = (newhits - hits, time.time())

def wasKilled(who):
    logging.info("cooldown: %s is killed on %d hits",who, config.cooldownOnKilled)
    setCooldown(who, config.cooldownOnKilled)

def didExit(who):
    logging.info( "cooldown: %s is exited on %d hits",who, config.cooldownOnExit)
    setCooldown(who, config.cooldownOnExit)

def systemBroken(target):
    global gTargets
    logging.info("cooldown: system %s broken" , target)
    gTargets[target] = time.time() + logic.systemAttackTimeout(target)

#def startedAttack(who):
#    setCooldown(who, 'attack', logic.getCooldownOnAttack(who))

def canEnter(who):
    who = unicode(who)
    if '@' in who: 
        who = utils.jidStrip(who)
    return not (who in gCooldowns) or gCooldowns[who][0] > 0

def canAttack(target):
    return (not (target in gTargets)) or time.time() > gTargets[target]

def getVitality(who):
    who = unicode(who)
    if '@' in who: 
        who = utils.jidStrip(who)
    if who in gCooldowns:
        hits = gCooldowns[who][0]
        #assert hits > 0
        return hits
    else:
        return logic.getVitality(who)

def updateCooldowns():
    now = time.time()
    remove = []
    for who in gCooldowns:
        if confs.getConfsCount(who) > 0:
            continue
        delta = int(now - gCooldowns[who][1])
        if delta > config.cooldownRestore:
            newhits = gCooldowns[who][0] + 1
            if newhits > logic.getVitality(who):
                logging.info("cooldown: user %s restored" , who)
                remove.append(who)
            else:
                #print "cooldown: user %s incremented (%d)" % (who, newhits)
                gCooldowns[who] = (newhits, now)
    for r in remove:
        del gCooldowns[r]
    remove = []
    for t in gTargets:
        if time.time() > gTargets[t]:
            remove.append(t)
    for r in remove:
            del gTargets[r]  
                
