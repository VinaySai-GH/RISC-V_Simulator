
import math
import random

class CacheLine:
    def __init__(self):
        self.valid=false
        self.tag=None
        self.last_used=0 # timestamp for lru logic

class CacheLevel:
    def __init__(self,name,size,block_size,associativity,latency,policy="LRU"):
        self.name=name
        self.size=size
        self.block_size=block_size
        self.associativity=associativity
        self.latency=latency
        self.policy=policy
        self.num_sets = size // (block_size * associativity)
        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(self.num_sets))
        self.sets=[[CacheLine() for _ in range(associativity)] for _ in range(self.num_sets)]
        self.hits=0
        self.misses=0
    def _get_parts(self,address):
        """Standard RISC-V bit-splitting"""
        index=(address >> self.offset_bits)&(self.num_sets-1)
        tag=address >> (self.offset_bits+self.index_bits)
        return tag,index

    def access(self,address,current_cycle):
       """Returns true if found(hit),false if not (miss)"""
       tag,index=self._get_parts(address)
       target_set=self.sets[index]
       for line in target_set:
            if line.valid and line.tag == tag:
                self.hits += 1
                line.last_used = current_cycle # Update for LRU
                return True
            self.misses+=1
            return False

    def update(self,address,current_cycle):
        """brings new data into the cache (handles eviction)"""
        tag,index=self._get_parts(address)
        target_set=self.sets[index]
       # 1. Find an empty slot if possible
        for line in target_set:
            if not line.valid:
                line.valid, line.tag, line.last_used = True, tag, current_cycle
                return
        # 2. If full, use Replacement Policy
        if self.policy=="LRU":
            # Evict the oldest one
           victim=min(target_set,key=lambda l:l.last_used)
        else: # Random choice
          victim=random.choice(target_set)
          victim.tag=tag
          victim.last_used=current_cycle
           
         
        
        
        
        
        


        
        
        
        

       
        
       
  
    

