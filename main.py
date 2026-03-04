import argparse
from utils.config_loader import load_config
from utils.assembler import Assembler

def main():
    parser = argparse.ArgumentParser(description="RISC-V Simulator")

    parser.add_argument("assembly_file", help="Path to the .asm file")

    parser.add_argument("--pipeline", dest="pipeline", action="store_true",
                        help="Enable pipelining")
    parser.add_argument("--no-pipeline", dest="pipeline", action="store_false",
                        help="Disable pipelining")

    parser.add_argument("--forwarding", dest="forwarding", action="store_true",
                        help="Enable data forwarding")
    parser.add_argument("--no-forwarding", dest="forwarding", action="store_false",
                        help="Disable data forwarding")

    config = load_config("config.json")
    parser.set_defaults(pipeline=config["pipeline"], forwarding=config["forwarding"])

    args = parser.parse_args()

    # Print current settings
    print(f"Pipeline:   {'ON' if args.pipeline else 'OFF'}")
    print(f"Forwarding: {'ON' if args.forwarding else 'OFF'}")
    print()

    # Load and parse the assembly file
    assembler = Assembler()
    instructions, labels = assembler.load(args.assembly_file)

    print(f"Labels found: {labels}")
    print(f"Instructions loaded: {len(instructions)}")
    for i, instr in enumerate(instructions):
        print(f"  line {i}: {instr}")

if __name__ == "__main__":
    main()