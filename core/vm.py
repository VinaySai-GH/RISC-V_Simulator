
class DTLB:
    def __init__(self, num_entries, policy="LRU"):
        self.num_entries = num_entries
        self.policy = policy.upper()
        # List of dicts: {"vpn": vpn, "pfn": pfn, "last_used": time, "inserted_at": time}
        self.entries = []

    def lookup(self, vpn, current_cycle):
        for entry in self.entries:
            if entry["vpn"] == vpn:
                entry["last_used"] = current_cycle
                return entry["pfn"]
        return None

    def insert(self, vpn, pfn, current_cycle):
        # Update if it already exists
        for entry in self.entries:
            if entry["vpn"] == vpn:
                entry["pfn"] = pfn
                entry["last_used"] = current_cycle
                return

        # Evict if full
        if len(self.entries) >= self.num_entries:
            if self.policy == "FIFO":
                victim = min(self.entries, key=lambda x: x["inserted_at"])
            else: # LRU default
                victim = min(self.entries, key=lambda x: x["last_used"])
            self.entries.remove(victim)

        self.entries.append({
            "vpn": vpn,
            "pfn": pfn,
            "last_used": current_cycle,
            "inserted_at": current_cycle
        })

    def invalidate(self, vpn):
        self.entries = [e for e in self.entries if e["vpn"] != vpn]


class VirtualMemorySystem:
    def __init__(self, config):
        vm_config = config.get("vm", {})
        mem_config = config.get("memory", {})
        
        self.page_size = mem_config.get("page_size_bytes", 4096)
        self.virtual_size = mem_config.get("virtual_size_bytes", 65536)
        self.physical_size = mem_config.get("physical_size_bytes", 16384)
        
        self.dtlb_entries = vm_config.get("dtlb_entries", 4)
        self.tlb_hit_latency = vm_config.get("tlb_hit_latency", 1)
        self.page_walk_latency = vm_config.get("page_walk_latency", 10)
        self.page_fault_latency = vm_config.get("page_fault_latency", 50)
        self.policy = vm_config.get("replacement_policy", "LRU").upper()
        
        self.num_frames = self.physical_size // self.page_size
        
        self.dtlb = DTLB(self.dtlb_entries, self.policy)
        self.page_table = {} # flat page table: vpn -> {"pfn": pfn, "valid": bool, "dirty": bool}
        
        # Physical memory management
        self.free_frames = list(range(self.num_frames))
        self.allocated_frames = [] # tracks frames for page replacement
        
        self.stats = {
            "tlb_hits": 0, "tlb_misses": 0, "page_walks": 0,
            "page_faults": 0, "page_evictions": 0, 
            "dirty_evictions": 0, "translation_penalty": 0
        }

    def translate(self, virtual_address, is_write, current_cycle):
        vpn = virtual_address // self.page_size
        offset = virtual_address % self.page_size
        
        latency = 0
        
        # 1. TLB Lookup
        latency += self.tlb_hit_latency
        pfn = self.dtlb.lookup(vpn, current_cycle)
        
        if pfn is not None:
            self.stats["tlb_hits"] += 1
        else:
            # 2. TLB Miss -> Page Walk
            self.stats["tlb_misses"] += 1
            self.stats["page_walks"] += 1
            latency += self.page_walk_latency
            
            pt_entry = self.page_table.get(vpn)
            
            if pt_entry and pt_entry["valid"]:
                pfn = pt_entry["pfn"]
            else:
                # 3. Page Fault -> Allocate Frame
                self.stats["page_faults"] += 1
                latency += self.page_fault_latency
                
                if self.free_frames:
                    pfn = self.free_frames.pop(0)
                else:
                    # Memory Full -> Page Replacement
                    self.stats["page_evictions"] += 1
                    if self.policy == "FIFO":
                        victim = min(self.allocated_frames, key=lambda x: x["inserted_at"])
                    else:
                        victim = min(self.allocated_frames, key=lambda x: x["last_used"])
                    
                    self.allocated_frames.remove(victim)
                    pfn = victim["pfn"]
                    victim_vpn = victim["vpn"]
                    
                    # Evict old page
                    if self.page_table[victim_vpn]["dirty"]:
                        self.stats["dirty_evictions"] += 1
                    self.page_table[victim_vpn]["valid"] = False
                    self.dtlb.invalidate(victim_vpn)

                # Update Page Table for the newly loaded page
                self.page_table[vpn] = {"pfn": pfn, "valid": True, "dirty": False}
                self.allocated_frames.append({
                    "pfn": pfn, "vpn": vpn,
                    "last_used": current_cycle, "inserted_at": current_cycle
                })

            # Load into TLB
            self.dtlb.insert(vpn, pfn, current_cycle)

        # Update dirty bit for writes
        if is_write:
            self.page_table[vpn]["dirty"] = True
            
        # Update LRU tracking for the physical frame
        for frame in self.allocated_frames:
            if frame["pfn"] == pfn:
                frame["last_used"] = current_cycle
                break

        self.stats["translation_penalty"] += int(latency)
        physical_address = int((pfn * self.page_size) + offset)
        
        return physical_address, int(latency)
