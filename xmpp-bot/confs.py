# -*- coding: utf-8 -*-
import time
import traceback
import random
import smtplib
import logging

import xmpp

import utils
import config
import logic
import cooldown
import background
from registry import Registry

from Queue import Queue

gConferences = {}

MAX_RESULT = 65535

def getConfsCount(person):
    cnt = 0
    for c in gConferences.itervalues():
        if person in c.offenders or person in c.defenders:
            cnt += 1
    return cnt 

class Person(object):
    __slots__ = ["name", "health", "last_attack", "attacks", "attacks_defended", "attacks_sucessful"]
    def __init__(self, name, health):
        self.name, self.health = name, health
        self.last_attack = 0
        self.attacks = {}
        self.attacks_defended, self.attacks_sucessful = 0,0

    def revive(self, value):
        self.health = value

    def __str__(self):
        return u"Person(name = %s, health = %d)" % (self.name, self.health)

    def isDead(self):
        return self.health <= 0

    def onExit(self, killed):
        if killed:
            cooldown.wasKilled(self.name)
        else:
            cooldown.didExit(self.name)
            self.health = -100

    def damage(self, conn, by, amount, conf):
        self.health -= amount
        self.attacks_sucessful += 1
        logging.info(u"damaged %s by %s by %d", self, by, amount)
        utils.sendConf(conn, conf.name, u"%s damages %s by %d" % (by.name, self.name, amount))
        if self.isDead() and by:
            background.getUrlBackground("hack_dead.php?", {"name":u"%s"%self.name,"n":str(logic.getHackerTagCount(self.attacks_defended, self.attacks_sucessful))}, conf)
            utils.sendPrivate(conn, self.name, u"You are terminated by %s" % by.name)

    def canAttack(self):
        return time.time() - self.last_attack > logic.getDirectAttackCooldown(self.name)

    def scheduleAttack(self, by, code, by_defender):
        self.attacks[time.time() + logic.getDirectAttackTime(by.name, self.name)] = (by, code, by_defender)
        if by.last_attack < time.time():
            by.last_attack = time.time()
        logging.info(u"scheduled attack for %s by %s" ,self, by)

    def doDefend(self, code):
        correctCode = "".join(reversed(code))
        for t in [k for k, v in self.attacks.items() if v[1] == correctCode]:
            logging.info(u"defended %s by %s" ,self, self.attacks[t][0])
            self.attacks_defended += 1
            del self.attacks[t]

    def idle(self, conn, conf):
        currentTime = time.time()
        for k, v in self.attacks.items():
            if currentTime >= k:
                self.damage(conn, v[0], logic.getDirectAttackDamage(v[0], self.name, v[2]), conf)
                del self.attacks[k]

class Conf(object):
    __slots__ = ["target", "name", "health", "next_question", "defenders", "offenders", "question", "start_time", "registry", "cooldowns",
                 "questions", "print_queue", "defeated_commands", "reward_person", "reward_timeout", "defeated_timeout", "cmd_request_sent",
                    "reward_cmd", "reward_args", "police_notify_sent", "stat_cooldown"]
    def __init__(self, target, name = None):
        self.target = target
        self.name = name if name else utils.randStr()
        self.health = logic.getSystemVitality(self.target)
        self.next_question = None
        self.start_time = None
        self.defenders = {}
        self.offenders = {}
#        self.cooldowns = {}
        self.questions = logic.getQuestions(self.target)
        self.question = None
        self.registry = Registry()
        self.print_queue = Queue()
        self.defeated_commands = None
        self.defeated_timeout = None
        self.reward_person = None
        self.reward_timeout = None
        self.reward_cmd = None
        self.reward_args = None
#        self.saved_message = None
        self.cmd_request_sent = None
        self.police_notify_sent = False
        self.stat_cooldown = None

    def sendPoliceNotify(self, target):
        if not self.police_notify_sent:
            msg = u"From: %s\nTo: %s\nContent-type: text/plain;charset=utf-8\nSubject: WARNING! Target is under attack\n\nTarget: %s\nAttack time: %s" % (config.fromEmail, config.policeEmail, target, time.ctime())
            msg = unicode(msg).encode('utf-8')
            s = smtplib.SMTP()
            s.connect(config.mailHost, config.mailPort)
            res = s.sendmail(config.fromEmail,config.policeEmail,msg)
            logging.info("police notify sent %s" , res)
            self.police_notify_sent = True            

#     def onExit(self, person):
#         self.cooldowns[person] = time.time() + logic.getCooldownOnExit(person, self.target)

#     def onEnter(self, conn, person, nickname):
#         if self.cooldowns.get(person, 0) > time.time():
#            utils.sendKick(conn, self.name, [nickname], u"Отдохни!")

    @utils.protect
    def onPresence(self, conn, person, nickname, alive):
        if alive:
            logging.info(u"%s comes to %s", person, self.target)
        if not self.registry.onPresence(person, nickname, alive) and self.findPerson(person):
            self.findPerson(person).onExit(False)
            self.dropPerson(person)
#            self.onExit(person)
#        else:
#            self.onEnter(conn, person, nickname)

    def revive(self):
        self.health = logic.getSystemVitality(self.target)
        [person.revive(logic.getVitality(person.name.getStripped())) for name, person in self.defenders.items()]
        self.police_notify_sent = False
        self.stat_cooldown = None

    def __str__(self):
        return u"Conference(target = %s, name = %s, health = %s, defenders = [%s], offenders = [%s])" % (self.target, self.name, self.health, ", ".join("(%s: %s)" % (k, v) for k, v in self.defenders.iteritems()), ", ".join("(%s: %s)" % (k, v) for k, v in self.offenders.iteritems()))

    def newOffender(self, p):
        if p not in self.offenders:
            if logic.policeNotifyOnAttack(p):
                self.sendPoliceNotify(self.target)
            self.offenders[p] = Person(p, cooldown.getVitality(p))

    def newDefender(self, p):
        if p not in self.defenders:
            self.defenders[p] = Person(p, cooldown.getVitality(p))

    def idle(self, conn):
        while not self.print_queue.empty():
            res = self.print_queue.get()
            logging.info(u"receive result: %s",unicode(res))
#            if timeout <= time.time():
            utils.sendConf(conn, self.name, res[:MAX_RESULT])
            if self.cmd_request_sent:
                utils.sendConf(conn, self.name, u"Time left: %d sec. Type command." % (int(self.defeated_timeout - time.time())))
                self.cmd_request_sent = None
 #           else:
#                self.saved_message = (timeout, res)
#                if self.defeated_timeout:
#                    utils.sendConf(conn, self.name, u"Time left: %d sec" % (int(self.defeated_timeout - time.time())))
        if self.defeated():
#            if self.saved_message and self.saved_message[0] <= time.time():
#                utils.sendConf(conn, self.name, self.saved_message[1])
#                self.saved_message = None                                              
            if not self.defeated_commands:
                background.getUrlBackground("hack_done.php?", {"hackers": ",".join(x.getNode() for x in self.offenders.keys()), "target": self.target})
                rewards, score = logic.getRewardAndScore(self.target, time.time() - self.start_time)
                self.defeated_timeout = time.time() + score
                self.defeated_commands = rewards
                self.reward_person = None
                self.reward_timeout = None
                self.cmd_request_sent = None
                self.kickDefenders(conn)
                utils.sendConf(conn, self.name, u"Hacking done. Time left: %d sec. Type command." % (score))
                logging.info(u"%s Hacking done. Time left: %d sec. Type command.", self.target, score)
            else:
                if time.time() > self.defeated_timeout:
                    utils.sendConf(conn, self.name, u"Hacking finished. Connection terminated.", lambda sess, s: utils.leaveConf(conn, self.name))
                    logging.info(u"%s Finish",self.target)
                    return True
                if self.reward_timeout and time.time() > self.reward_timeout and not self.cmd_request_sent:
                    self.cmd_request_sent = True
                    background.getUrlBackground("hack_cmd.php?", {"target": self.target, "cmd": self.reward_cmd, "args": " ".join(self.reward_args)}, self)

        if not self.offenders:
            self.revive()
            self.next_question = None
            self.start_time = None
        for l in [self.defenders, self.offenders]:
            [p.idle(conn, self) for p in l.values()]

        self.kickDeads(conn)
        
        if len(self.offenders) == 0 and len(self.defenders) == 0:
            return True

        if not self.defeated(): 
            currentTime = time.time()
            if not self.next_question:
                if self.offenders:
                    self.start_time = currentTime
                    self.next_question = currentTime + random.randint(1, config.nextQuestionMaxTimeout)
            else:
                if currentTime > self.next_question:
                    if self.question and self.offenders:
                        person = random.choice(self.offenders.values())
                        person.damage(conn, Person(config.nickname,0), logic.getSystemDamage(person, self.target, self.question), self)
                        if logic.policeNotifyOnDamage(person.name):     
                            self.sendPoliceNotify(self.target)
                    self.question = self.nextQuestion()
                    logging.info('%s: new question: %s',self.target, self.question.text)
                    self.next_question = currentTime + self.question.timeout
                    utils.sendConf(conn, self.name, self.question.text)
            return False

    def nextQuestion(self):
        return random.choice(self.questions)

    def defeated(self):
        return self.health <= 0

    def kickDefenders(self, conn):
        for jid, d in self.defenders.iteritems():
            d.revive(0)
        self.kickDeads(conn)

    def kickDeads(self, conn):
        toKick = []
        for l in [self.offenders, self.defenders]:
            toDelete = []
            for name, person in [x for x in l.iteritems() if x[1].isDead()]:
                toKick.append(self.registry.getNick(person.name))
                person.onExit(True)
                toDelete.append(name)
                if logic.policeNotifyOnKill(name):
                    self.sendPoliceNotify(self.target)                                        
            for x in toDelete:
                del l[x]
        utils.sendKick(conn, self.name, toKick, u"Terminated!")
                
    def findPerson(self, person):
        for l in [self.offenders, self.defenders]:
            if person in l:
                return l[person]
        return None

    def dropPerson(self, person):
        for l in [self.offenders, self.defenders]:
            if person in l:
                del l[person]
                return                                   

    def findRandomDefender(self, person, me):
        l = []
        exclude = unicode(me.name) if me else ''
        for n,v in self.defenders.iteritems():
            name = unicode(v.name)
            if name[:len(person)] == person and name[:len(exclude)] != exclude:  
                l.append(v)
        return random.choice(l) if len(l) > 0 else None

    def findRandomOffender(self, person, me):
        l = []
        exclude = unicode(me.name) if me else ''
        for n,v in self.offenders.iteritems():
            name = unicode(v.name)
            if name[:len(person)] == person and name[:len(exclude)] != exclude:
                l.append(v)
        return random.choice(l) if len(l) > 0 else None

    def onMessage(self, conn, msg):
        res = msg.getFrom().getResource()
        if not res: 
            return
        if msg.getType() != 'groupchat' or not msg.getBody():
            return
        person = self.registry[res]
        if not self.findPerson(person):
            return
        logging.info(u"%s message from %s: %s",self.target ,person, msg.getBody())
        if not self.defeated_commands and self.question and utils.sEq(msg.getBody(), self.question.answer):            
            if person in self.offenders:
                damage = logic.getDamage(person, self.target, self.question)
                self.health -= damage
                if not self.defeated():
                    utils.answerConf(conn, msg, u"System damaged: %d, left: %d" % (damage, self.health))
                    logging.info(u"%s System damaged: %d, left: %d",self.target,damage, self.health)
                else:
                    cooldown.systemBroken(self.target)
            else:
                return
            self.question = None
            self.next_question = time.time() + random.randint(1, config.nextQuestionMaxTimeout)
        else:
            if not msg.getBody(): return
            parts = [utils.normalize(x) for x in msg.getBody().strip().split(" ")]
            if parts:
                if self.defeated_commands and parts[0] in logic.availableRewards():
                    if parts[0] in self.defeated_commands:
                        if not self.reward_person:
                            self.rewardCommand(conn, person, parts[0], parts[1:])
                    else:
                        utils.answerConf(conn, msg, u"Command %s is unsupported by target. Time left: %d" % (parts[0], int(self.defeated_timeout - time.time())))
                else:
                    {"stat": self.printStats, "attack": self.scheduleAttack, "defend": self.doDefend}.get(parts[0], lambda x, y, z: None)(conn, person, parts[1:])
    
    def printStats(self, conn, person, args):
        now = time.time()
        if self.stat_cooldown == None or now > self.stat_cooldown:
            userlist = []
            for d in self.defenders.itervalues():
                userlist.append("defender\t%s\t%s" % (d.name,d.health))
            for o in self.offenders.itervalues():  
                userlist.append("offender\t%s\t%s" % (o.name,o.health))
            msg = u"Conference info:\ntarget\t%s\nhealth\t%s\n\n%s" % (self.target, self.health, "\n".join(userlist))
            utils.sendConf(conn, self.name, unicode(msg))
            self.stat_cooldown = now + config.statCommandCooldown

    def scheduleAttack(self, conn, person, args):
        attackPerson = self.findPerson(person)
        if not attackPerson or not attackPerson.canAttack():
            return
        if len(args) < 2: return
        try:
            code, target = args[0], args[1]
            if len(code) == config.codeLength and int(code) >= 0:
                if person in self.offenders:
                    targetPerson = self.findRandomDefender(target, attackPerson)
                    if not targetPerson:
                        targetPerson = self.findRandomOffender(target, attackPerson)
                elif person in self.defenders:
                    targetPerson = self.findRandomOffender(target, attackPerson)
                else:
                    return
                if targetPerson:
                    targetPerson.scheduleAttack(attackPerson, code, person in self.defenders)
        except:
            logging.exception('e')

    def doDefend(self, conn, person, args):
        defenderPerson = self.findPerson(person)
        if not defenderPerson:
            return
        if len(args) < 1: return
        try:
            code = args[0]
            if len(args) == 2:
                target = args[1]
                if person in self.offenders:
                    targetPerson = self.findRandomDefender(target, '')
                    if not targetPerson:
                        targetPerson = self.findRandomOffender(target, '')
                elif person in self.defenders:
                    targetPerson = self.findRandomOffender(target, '')
                    if not targetPerson:
                        targetPerson = self.findRandomDefender(target, '')
                else:
                    return
            else:
                targetPerson = defenderPerson
            targetPerson.doDefend(code)
        except:
            logging.exception('e')
            
    def rewardCommand(self, conn, person, cmd, args):
        rewardPerson = self.findPerson(person)
        if not rewardPerson:
            return
        self.reward_person = rewardPerson
        self.reward_timeout = time.time() + logic.getCommandTime(cmd)
        self.reward_cmd = cmd
        self.reward_args = args

    def backgroundDone(self, res):
        res = res.decode('utf-8')
        self.print_queue.put((res))
        if self.reward_person and time.time() > self.reward_timeout:
            self.reward_person = None
            self.reward_timeout = None

def getConfs():
    global gConferences
    return gConferences

def getConfByTarget(targetRaw):
    target = utils.normalize(targetRaw)
    if target in getConfs():
        return getConfs()[target]
    newConf = Conf(target)
    logging.info(u"%s Conf started",unicode(newConf))
    getConfs()[target] = newConf
    return newConf

def getConfByName(name):
    ret = [c for (t, c) in getConfs().iteritems() if utils.sEq(c.name, name)]
    if ret:
        return ret[0]
    return None
