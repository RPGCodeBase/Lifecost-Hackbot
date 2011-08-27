import xmpp
import utils
import logging
#import random

class Registry(object):
    __slots__ = ["persons","real_persons"]
    def __init__(self):
        self.persons = {}
        self.real_persons = {}
        
    def onPresence(self, person, nickname, is_alive):
        nickname = unicode(nickname)
        jid = person.getStripped()
        hackername = utils.jidStrip(jid)        
        if is_alive:
            if nickname in self.persons:
                logging.info(u"there is already %s with nickname %s" ,self.persons[nickname], nickname)
            self.persons[nickname] = person
            self.real_persons[hackername] = person
            logging.info(u"Registering %s with nickname %s" % (self.persons[nickname], nickname))
        else:
            if nickname in self.persons:
                del self.persons[nickname]
                del self.real_persons[hackername]
                return False
        return True

    def __str__(self):
        return (u"Registry: " + u", ".join(["%s: %s" % (k, v) for k, v in self.persons.items()])).encode("utf-8")
    
    def containsHacker(self, hackname):
        return hackname in self.real_persons
    def getHacker(self, hackname):
        return self.real_persons[hackname]

    def __getitem__(self, nickname):
        nickname = unicode(nickname)
        return self.persons[nickname]
        
    def __contains__(self, nickname):
        return nickname in self.persons
        
#    def getRandomItem(self, nickname, exclude):
#        nickname = unicode(nickname)
#        l = list((v for n,v in self.persons.iteritems() if (n[len(nickname):] == nickname and n[len(exclude):] != exclude)))
#        print list(n for n,v in self.persons.iteritems())
#        return random.choice(l)

    def getNick(self, jid):
        ret = [n for n, p in self.persons.items() if p == jid]
        if ret:
            return ret[0]
        return None
