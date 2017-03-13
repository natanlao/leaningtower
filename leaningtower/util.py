# -*- coding: utf-8 -*-
from functools import wraps
import logging
import os
import time

log = logging.getLogger(__name__)


# http://blog.gregburek.com/2011/12/05/Rate-limiting-with-decorators/
def limit_rate(interval):
    def decorate(func):
        lastTimeCalled = [0.0]

        def rateLimitedFunction(*args, **kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = interval - elapsed
            if leftToWait > 0:
                time.sleep(leftToWait)
            ret = func(*args, **kargs)
            lastTimeCalled[0] = time.clock()
            return ret

        return rateLimitedFunction

    return decorate


# This implementation sucks and should be fixed
def cache(subdir, filename, inherit_filename=False):
    # Ensure necessary directories exist
    subdir = os.path.join("cache", subdir)
    if not os.path.exists(subdir):
        os.makedirs(subdir)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            fname = filename
            if inherit_filename:
                fname = str(args[int(filename)]) + ".html"
            fpath = os.path.join(subdir, fname)
            if os.path.exists(fpath):
                log.info("Cache hit for %s", fname)
                return open(fpath, "r")
            kwargs['filename'] = fpath
            return func(*args, **kwargs)
        return wrapper
    return decorator
