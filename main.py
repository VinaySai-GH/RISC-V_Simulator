import argparse
from utils.config_loader import load_config
from utils.assembler import Assembler
from simulator.pipeline import Pipeline

def main():
    parser = argparse.ArgumentParser(description="RISC-V Simulator")
    parser.add_argument("assembly_file", help="Path to .asm file")
    parser.add_argument("--pipeline",
                        dest="pipeline", action="store_true")
    parser.add_argument("--no-pipeline",
                        dest="pipeline", action="store_false")
    parser.add_argument("--forwarding",
                        dest="forwarding", action="store_true")
    parser.add_argument("--no-forwarding",
                        dest="forwarding", action="store_false")

    config = load_config("config.json")
    parser.set_defaults(
        pipeline=config["pipeline"],
        forwarding=config["forwarding"])
    args = parser.parse_args()

    print(f"Pipeline:   {'ON' if args.pipeline else 'OFF'}")
    print(f"Forwarding: {'ON' if args.forwarding else 'OFF'}")

    assembler = Assembler()
    instructions, labels = assembler.load(args.assembly_file)

    print(f"Labels found: {labels}")
    print(f"Instructions loaded: {len(instructions)}")
    for i, instr in enumerate(instructions):
        print(f"  line {i}: {instr}")

    sim = Pipeline(
        instructions, labels,
        args.pipeline, args.forwarding, config)
    sim.run()

if __name__ == "__main__":
    main()
