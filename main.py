# main.py
import argparse
from utils.config_loader import load_config
from utils.assembler import Assembler
from simulator.pipeline import Pipeline
from simulator.trace_replay import TraceReplayer

def main():
    parser = argparse.ArgumentParser(description="RISC-V Simulator")
    parser.add_argument("file", help="Path to .asm file or .trace file")
    parser.add_argument("--trace", action="store_true", help="Run in Trace Replay mode for Phase 3")
    parser.add_argument("--config", default="config.json", help="Path to config file (.json or .ini)")
    parser.add_argument("--pipeline", dest="pipeline", action="store_true")
    parser.add_argument("--no-pipeline", dest="pipeline", action="store_false")
    parser.add_argument("--forwarding", dest="forwarding", action="store_true")
    parser.add_argument("--no-forwarding", dest="forwarding", action="store_false")

    args = parser.parse_args()
    config = load_config(args.config)
    
    parser.set_defaults(
        pipeline=config.get("pipeline", True),
        forwarding=config.get("forwarding", True)
    )
    args = parser.parse_args()

    # Route based on execution mode
    if args.trace:
        sim = TraceReplayer(args.file, config)
        sim.run()
    else:
        print(f"Pipeline:   {'ON' if args.pipeline else 'OFF'}")
        print(f"Forwarding: {'ON' if args.forwarding else 'OFF'}")

        assembler = Assembler()
        instructions, labels = assembler.load(args.file)
        sim = Pipeline(instructions, labels, args.pipeline, args.forwarding, config)
        sim.run()

if __name__ == "__main__":
    main()
