#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import xmpp

from confs import getConfs, getConfByTarget, getConfByName, getConfsCount
from utils import sEq, answerPrivate, answerConf, getConferenceJid, normalize, protect
from registry import Registry
from logic import *
import time
import logging

import config
import cooldown
import background
import subscribe

registry = Registry()
subscribe = subscribe.Subscribe()

def onPrivateMessage(conn, msg):
    answerPrivate(conn, msg, u"I'm not a bot!")

@protect
def onMessage(conn, msg):
    if msg.getFrom().getDomain() != config.conference:
        onPrivateMessage(conn, msg)
        raise xmpp.NodeProcessed
        return 

    if msg.getFrom().getNode() != config.mainChannel:
        onBattleMessage(conn, msg, msg.getFrom().getNode())
        raise xmpp.NodeProcessed
        return 

    processCommand(conn, msg, msg.getBody())
    raise xmpp.NodeProcessed

@protect
def onPresence(conn, msg):
    if msg.getFrom().getDomain() == config.conference:
        conf, nickname = msg.getFrom().getNode(), msg.getFrom().getResource()
        role = msg.getTag("x", namespace = xmpp.NS_MUC_USER)
        if role and role.getTag("item").getAttr("jid"):
            person = xmpp.JID(role.getTag("item").getAttr("jid"))
            alive = role.getTag("item").getAttr("role") != "none" and msg.getAttr("type") != "unavailable"
            #print "%s: %s is %s and is he alive: %s" % (conf, person, nickname, alive)
            if conf == config.mainChannel:
                registry.onPresence(person, nickname, alive)
            else:
                confObj = getConfByName(conf)
                if confObj:
                    confObj.onPresence(conn, person, nickname, alive)
    raise xmpp.NodeProcessed

def onBattleMessage(conn, msg, confName):
    conf = getConfByName(confName)
    if conf:
        conf.onMessage(conn, msg)

@protect
def sendInvite(conn, to, conf):
    logging.info("Invite: %s tg: %s ",to,conf)
    invite = xmpp.Message(to = xmpp.JID(node = conf, domain = config.conference))
    invite.setTag('x', namespace = xmpp.NS_MUC_USER).setTag('invite', {'to': to})
    conn.send(invite)

@protect
def sendSubscription(conn, to_jid, target):
    msg = xmpp.Message(to = to_jid, body = u"Subscribed target %s is under attack!" % (target)) 
    conn.send(msg)

def processCommand(conn, msg, msgText):
    if not msgText: return
    parts = [normalize(x) for x in msgText.strip().split(" ")]
    name = msg.getFrom().getResource()
    if not name:
        return
    if name not in registry:
        return
    logging.info("Command from %s: %s",name,msgText)
    person = registry[name]
    jid = person.getStripped()
    hackername = utils.jidStrip(jid)
    if len(parts) == 3:
        cmd, target, action = parts
        is_defend = sEq(action, u"defend")
        is_offend = sEq(action, u"attack")
        if sEq(cmd, "connect") and (is_offend or is_defend):
            hour = time.localtime().tm_hour
            if hour >= config.nightSleepHour and hour < config.morningStartHour:
                answerPrivate(conn, msg, u"Cool down, guy! Time to sleep for a while... Back to work at 9 a.m.")
                return
            if isValidTarget(name, target) and getConfsCount(person) < allowedChannelsCount(jid):
                if not cooldown.canEnter(person):
                    answerPrivate(conn, msg, u"Cool down, guy! Take a beer...")
                    logging.info( u"Cool down, guy! Take a beer... %s", hackername)
                    return
                if is_offend and (not cooldown.canAttack(target)):
                    answerPrivate(conn, msg, u"Target was broken recently. It's impossible to hack it for now.")
                    logging.info(u"Target was broken recently. It's impossible to hack it for now. %s", hackername)
                    return
                conf = getConfByTarget(target)
                if not conf.defeated():
                    joinConference(conn, config.conference, conf.name, config.nickname)
                    sendInvite(conn, person, conf.name)
                    if is_offend:
                        conf.newOffender(person)
#                        cooldown.startedAttack(person)
                        subs = subscribe.subscribersFor(target)
                        for p in subs:
                            if registry.containsHacker(p) and p != hackername:
#                                print "SUBS %s"%p
                                sendSubscription(conn, registry.getHacker(p), target)
                                    
                    else:
                        conf.newDefender(person)
                logging.info(u"CONF STARTED: %s" ,conf)
            else:
                answerPrivate(conn, msg, u"Access denied.")
    elif len(parts) == 2:
        cmd, target = parts
        if sEq(cmd, "subscribe"):
            if subscribe.canSubscribe(hackername, target):
                subscribe.add(hackername, target)
                answerPrivate(conn, msg, u"Target %s subscribed." % (target))
            else:
                answerPrivate(conn, msg, u"Too many subscriptions.")
        elif sEq(cmd, "unsubscribe"):
            if subscribe.remove(hackername, target):
                answerPrivate(conn, msg, u"Target %s unsubscribed." % (target))
            else:
                answerPrivate(conn, msg, u"Target %s isn't subscribed." % (target))
    elif len(parts) == 1:
        cmd = parts[0]
        if sEq(cmd, "subscriptions"):
            txt = u"List of subscriptions:\n"
            for s in subscribe.subscriptionsOf(hackername):
                txt += u"%s\n" % (s)
            answerPrivate(conn, msg, txt)
        elif sEq(cmd, "status"):
            txt = u"Current personal status: %d" % cooldown.getVitality(hackername)
            answerPrivate(conn, msg, txt)
                
def doStep(conn):
    try:
        return conn.Process(10)
    except KeyboardInterrupt: 
        return 0

def doIdle(conn):
    try:
        toDelete = []
        for target, conf in getConfs().iteritems():
            if conf.idle(conn):
                toDelete.append(target)

        cooldown.updateCooldowns()

        for t in toDelete:
            del getConfs()[t]
    except KeyboardInterrupt: 
        return 0
    return 1

def joinConference(conn, server, room, nickname, password = "", public = False):
    p = xmpp.Presence(to = xmpp.JID(node = room, domain = server, resource = nickname))
    p.setTag('x',namespace=xmpp.NS_MUC).setTagData('password', password)
    p.setTag('x',namespace=xmpp.NS_MUC).setTagData('anonymous', False)
    p.setTag('x',namespace=xmpp.NS_MUC).setTagData('public', public)
    p.setTag('x',namespace=xmpp.NS_MUC).setTagData('public_list', public)
    p.setTag('x',namespace=xmpp.NS_MUC).setTagData('allow_visitor_nickchange', False)
    p.getTag('x').addChild('history',{'maxchars':'0','maxstanzas':'0'})
    conn.send(p)


def main(name):
    if len(sys.argv)<3:
        print u"Usage: bot.py username@server.net password [logfile]"
    else:
        background.start()

        jid = xmpp.JID(node = sys.argv[1], domain = config.server, resource = "LC")
        user, server, password = jid.getNode(), jid.getDomain(),sys.argv[2]

        conn = xmpp.Client(server)
        conres = conn.connect()
        if not conres:
            logging.error(u"Unable to connect to server %s!",server)
            return 1
        if conres<>'tls':
            logging.warning(u"Warning: unable to estabilish secure connection - TLS failed!")
        
        authres = conn.auth(user,password)
        if not authres:
            logging.error(u"Unable to authorize on %s - check login/password.",server)
            return 1
        if authres != 'sasl':
            logging.error(u"Warning: unable to perform SASL auth os %s. Old authentication method used!",server)

        conn.RegisterHandler('message', onMessage)
        conn.RegisterHandler('presence', onPresence)
        conn.sendInitPresence()
        joinConference(conn, config.conference, room = config.mainChannel, nickname = name, password = "", public = True)
        logging.info("Bot started.")

        counter = 1
        while True:
   #         counter = 20                        
            if not conn.isConnected(): conn.reconnectAndReauth()
            result = doStep(conn)
            if result == 0:
                break;
            if result == '0':
                if doIdle(conn) == 0:
                    break;
#                counter = 20
 #           else:
  #              counter -= 1
#            print "Iteration: %s %s"%(repr(result),time.strftime('%H:%M:%S'))
#                print "Idle iter: %s "%(time.strftime('%H:%M:%S'))


if __name__ == "__main__":
    if len(sys.argv) > 3:
        logging.basicConfig(filename=sys.argv[3],format= "%(asctime)s %(levelname)s:%(message)s", datefmt="%D %H:%M:%S")
        print "logging to ",sys.argv[3]
    else:
        logging.basicConfig(format= "%(asctime)s %(levelname)s:%(message)s", datefmt="%D %H:%M:%S")
    logging.getLogger().setLevel(logging.DEBUG)    
    sys.exit(main(config.nickname))
