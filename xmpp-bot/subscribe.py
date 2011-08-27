import MySQLdb as db
import logic
import traceback
import utils

class Subscribe:
    def connect(self):
        self.db = db.connect(host='127.0.0.1',user='hack',passwd='Cij4bidwefhu',port = 3306, db='hack', charset="utf8")
        self.db.query('SET NAMES utf8') 
    
    def __init__(self):
        self.connect()
    
    def add(self, person, target):
        name = str(person)
        try:
            self.db.cursor().execute(u"REPLACE INTO subs (hacker,target) VALUES (%s,%s)",(name,target))
        except:
            logging.exception('e')
            self.connect()
        
    def remove(self, person, target):
        name = str(person)
        try:
            self.db.cursor().execute(u"DELETE FROM subs WHERE  hacker = %s and target = %s",(name,target))
        except:
            logging.exception('e')
            self.connect()
        if self.db.affected_rows() > 0:
            return True
        else:
            return False

    def count(self, person):
        name = str(person)
        count = 0
        try:
            u = self.db.cursor()
            u.execute(u"SELECT COUNT(*) FROM subs WHERE hacker = %s",(name,))
            count = u.fetchall()[0][0]
        except:
            logging.exception('e')
            self.connect()
        return count

    def subscribersFor(self, target):
        res = []
        try:
            u = self.db.cursor()
            u.execute(u"SELECT hacker FROM subs WHERE target = %s",(target,))
            res = [r[0] for r in u.fetchall()]
        except:
            logging.exception('e')
            self.connect()
        return res

    def subscriptionsOf(self, person):
        res = []
        try:
            u = self.db.cursor()
            u.execute(u"SELECT target FROM subs WHERE hacker = %s",(person,))
            res = [r[0] for r in u.fetchall()]
        except:
            logging.exception('e')
            self.connect()
        return res
    
    def canSubscribe(self, person, target):
        name = str(person)
        return self.count(name) < logic.hackerSubscribeCount(name)
