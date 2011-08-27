import traceback
import urllib2
import threading
import time
import logging

import config

from Queue import Queue

gQ = Queue()
def schedule(job):
    gQ.put(job)

def startForever(fn, timeout):
    def impl():
        while True:
            try:
                fn()
            except:
                 logging.exception('e')
            time.sleep(timeout)

    t = threading.Thread(target = impl)
    t.daemon = True
    t.start()

def start():
    def impl():
        job = gQ.get()
        job()
    return startForever(impl, 0)

def getUrl(url, args = None):
    getArgs = "&".join(["%s=%s" % (urllib2.quote(unicode(k).encode('utf-8')), urllib2.quote(unicode(v).encode('utf-8'))) for k, v in args.items()]) if args else ""
    try:
        url = "%s%s%s" % (config.baseUrl, url, getArgs)
        data = urllib2.urlopen(url).read()
        return data
    except:
        logging.exception('e')
    return None

def getUrlBackground(url, args = None, conf = None):
    def impl():
        res = getUrl(url, args)
        if conf:
            conf.backgroundDone(res)
    schedule(impl)

