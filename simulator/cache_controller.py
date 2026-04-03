
from core.cache import CacheLevel

class CacheController:
    def __init__(self,config):
        c=config["cache"]
        p=c["replacement_policy"]
        self.mem_lat=c["memory_latency"]
        self.l1i=CacheLevel("L1I",**c["L1I"],policy=p)
        self.l1d=CacheLevel("L1D",**c["L1D"],policy=p)
        self.l2  = CacheLevel("L2",  **c["L2"],  policy=p)
    def fetch_instruction(self, addr, cycle):
        return self._search(addr, self.l1i, cycle)
    
    def access_data(self,addr,cycle):
        return self._search(addr,self.l1d,cycle)

    def _search(self,addr,l1,cycle):
        
        latency=0
 
        latency+=l1.latency
        if l1.access(addr,cycle):
          return latency
      
        latency+=self.l2.latency
        if self.l2.access(addr,cycle):
          l1.update(addr,cycle)
          return latency

        latency += self.mem_lat
        self.l2.update(addr, cycle) 
        l1.update(addr, cycle)      
        return latency
       
          
        