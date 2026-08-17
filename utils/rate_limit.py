import time
class RateLimiter:
    def __init__(self,seconds=1): self.seconds=seconds; self.last={}
    def allow(self,key):
        t=time.monotonic()
        if t-self.last.get(key,0)<self.seconds: return False
        self.last[key]=t; return True
