import json
import configparser
import os
 
def load_config(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"config file not found: {file_path}")
    
    if file_path.endswith('.ini'):
        return _load_ini(file_path)
    else:
        return _load_json(file_path)

def _load_json(file_path):
    with open(file_path, "r") as f:
        config = json.load(f)
    return config

def _load_ini(file_path):
    parser = configparser.ConfigParser()
    parser.read(file_path)
        
    config = {
        "pipeline": parser.getboolean("pipeline", "forwarding_enabled", fallback=True),
        "forwarding": parser.getboolean("pipeline", "forwarding_enabled", fallback=True),
        "latencies": {},
        "memory": {},
        "vm": {},
        "cache": {
            "replacement_policy": "LRU",
            "memory_latency": 100,
            "L1I": {"size": 4096, "block_size": 64, "associativity": 1, "latency": 1},
            "L1D": {"size": 4096, "block_size": 64, "associativity": 1, "latency": 1},
            "L2": {"size": 65536, "block_size": 64, "associativity": 8, "latency": 10}
        }
    }
      # Fill in the latencies (ADD, MUL, etc.)
    if "latencies" in parser:
        for key, val in parser["latencies"].items():
            config["latencies"][key.upper()] = int(val)
            
    # Fill in the memory settings
    if "memory" in parser:
        for key, val in parser["memory"].items():
            config["memory"][key] = int(val)
            
    # Fill in the VM settings
    if "vm" in parser:
        for key, val in parser["vm"].items():
            if key == "replacement_policy":
                config["vm"][key] = val
            else:
                config["vm"][key] = int(val)
                
    # Fill in the cache settings from INI
    if "cache" in parser:
        c = parser["cache"]
        if "l1_size_bytes" in c:
            config["cache"]["L1D"]["size"] = int(c["l1_size_bytes"])
            config["cache"]["L1I"]["size"] = int(c["l1_size_bytes"])
        if "l1_latency" in c:
            config["cache"]["L1D"]["latency"] = int(c["l1_latency"])
            config["cache"]["L1I"]["latency"] = int(c["l1_latency"])
        if "block_size_bytes" in c:
            size = int(c["block_size_bytes"])
            config["cache"]["L1D"]["block_size"] = size
            config["cache"]["L1I"]["block_size"] = size
            config["cache"]["L2"]["block_size"] = size
        if "associativity" in c:
            config["cache"]["L1D"]["associativity"] = int(c["associativity"])
            config["cache"]["L1I"]["associativity"] = int(c["associativity"])
        if "l2_size_bytes" in c:
            config["cache"]["L2"]["size"] = int(c["l2_size_bytes"])
        if "l2_latency" in c:
            config["cache"]["L2"]["latency"] = int(c["l2_latency"])
        if "l2_associativity" in c:
            config["cache"]["L2"]["associativity"] = int(c["l2_associativity"])

    return config
        

