# -*- coding: utf-8 -*-
import config
import random
import utils
import math
import background
import json

gData = {
    "targets": 
    {"test": 
     {"questions": [{"text": "1 - 1 = ", "answer": "0", "level": 1}, {"text": "2 * 2 = ", "answer": "4", "level": 2}, {"text": "3 * 3 * 3 = ", "answer": "27", "level": 3}, {"text": "4 * 4 = ", "answer": "16", "level": 2}],
      "rewards": ["showmoney","smallmoney","healthget","lasttransactions", "alltransactions","healthadd","bigmoney", "deface"],
      "level": 0
      }
     },
    "hackers":
        {"florens":
             {"level": 2}
        },
    "questions":
        [{"text": "2 + 2 = ", "answer": "4", "level": 1}, {"text": "3 + 3 = ", "answer": "6", "level": 1}, {"text": "4 + 4 = ", "answer": "8", "level": 1}, {"text": "5 + 5 = ", "answer": "10", "level": 1}]
    }

def forTarget(v, target, decrease = False):
    lvl = float(gData["targets"][target]["level"])
    if decrease:
        return v / math.pow(2, lvl)
    else:
        return v * math.pow(2, lvl)

def forHacker(v, hacker, decrease = False):
    name = str(hacker)
    if '@' in name:
        name = utils.jidStrip(hacker)
    lvl = float(gData["hackers"][name]["level"])
    if decrease:
        return v / math.pow(2, lvl)
    else:
        return v * math.pow(2, lvl)

def isValidTarget(person, target):
    person = utils.jidStrip(person)
    return target in gData["targets"]

def getSystemVitality(target):
    lvl = float(gData["targets"][target]["level"])
    return config.systemVitality[lvl]

def getVitality(hacker):
#    hacker = utils.jidStrip(hacker)
    lvl = getHackerLevel(hacker)
    return config.hackerVitality[lvl]

#def getVitalityDefend(person, target):
#    person = utils.jidStrip(person)
#    return forHacker(config.defenderVitality, person)

def getDamage(person, target, question):
    person = utils.jidStrip(person)
    return int(forHacker(config.offenderDamage, person)*config.questionFactor[question.level])

def getSystemDamage(person, target, question):
    lvl = int(gData["targets"][target]["level"])
    return int(config.systemAttack[lvl]*config.questionFactor[question.level])
    
def getDefenderDamage(person, target):
    person = utils.jidStrip(person)
    return config.defenderDamage

def getRewardAndScore(target, seconds):
    maxSeconds = forTarget(config.defendSystemTime, target)
    rewards = gData["targets"][target]["rewards"]
    if seconds <= maxSeconds / 2:
        score = config.rewardBaseScore * 5
    elif seconds <= maxSeconds:
        score = config.rewardBaseScore * 2
    else:
        score = config.rewardBaseScore
    return rewards, score

def availableRewards():
    return config.rewardCommandTimeout.keys()

def getHackerLevel(hacker):
    name = str(hacker)
    if '@' in name:
        name = utils.jidStrip(hacker)
    return int(gData["hackers"][name]["level"])

def allowedChannelsCount(hacker):
    lvl = getHackerLevel(hacker)
    return config.channelsCount[lvl]   

def hackerSubscribeCount(hacker):
    lvl = getHackerLevel(hacker)
    return config.subscriptionsCount[lvl]

def getCommandTime(cmd):
    return config.rewardCommandTimeout[cmd]

def getDirectAttackCooldown(person):
    person = utils.jidStrip(person)
    return config.directAttackCooldown

def getDirectAttackTime(atttacker, attackee):
    return config.directAttackTime

def getDirectAttackDamage(attacker, attackee, by_defender):
    return config.directAttackDamageDefender if by_defender else config.directAttackDamageOffender

def systemAttackTimeout(target):
    lvl = int(gData["targets"][target]["level"])
    return config.cooldownSystemAttack[lvl]

def policeNotifyOnAttack(hacker):
    hacker = utils.jidStrip(hacker)
    lvl = getHackerLevel(hacker)
    return lvl == 1

def policeNotifyOnDamage(hacker):      
    hacker = utils.jidStrip(hacker)
    lvl = getHackerLevel(hacker)
    return lvl == 2

def policeNotifyOnKill(hacker):
    hacker = utils.jidStrip(hacker)  
    lvl = getHackerLevel(hacker)
    return lvl == 3

#def getCooldownHitsOnExit():
#    person = utils.jidStrip(person)
#    return config.cooldownOnExit

#def getCooldownHitsOnKilled():
#    person = utils.jidStrip(person)
#    return config.cooldownOnKilled

#def getCooldownOnAttack(person):
#    person = utils.jidStrip(person)
#    return config.cooldownOnAttack

class Question(object):
    __slots__ = ["timeout", "text", "level", "answer"]
    def __init__(self, target, text, answer, level):
        self.text, self.answer, self.level = text, answer, float(level)
        lvl = int(gData["targets"][target]["level"])
        self.timeout = config.questionTime[lvl]

def getQuestions(target):
    specialQuestions = [Question(target, **x) for x in gData["targets"][target]["questions"]]
    commonQuestions = [Question(target, **x) for x in gData["questions"]]
    random.shuffle(specialQuestions)
    random.shuffle(commonQuestions)
    questions = (specialQuestions*3 + commonQuestions)[:30]
    #random.shuffle(questions)
    return questions

def getHackerTagCount(attacks_defeated, attacks_successful):
    perc = float(attacks_successful)/float(attacks_defeated+attacks_successful);
    return int(4*perc)

def updateData():
    global gData
    gData = json.loads(background.getUrl("hack_data.php"))
    pass

background.startForever(updateData, 10)
