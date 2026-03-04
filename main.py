import argparse
from utils.config_loader import load_config

def main():
    parser = argparse.ArgumentParser(description="RISC-V Simulator")

    parser.add_argument("assembly_file", help="Path to the .asm file")

    parser.add_argument("--pipeline", dest="pipeline", action="store_true",
                        help="Enable pipelining")
    parser.add_argument("--no-pipeline", dest="pipeline", action="store_false",
                        help="Disable pipelining")

    parser.add_argument("--forwarding", dest="forwarding", action="store_true",
                        help="Enable data forwarding (only with --pipeline)")
    parser.add_argument("--no-forwarding", dest="forwarding", action="store_false",
                        help="Disable data forwarding")

    # Load defaults from config.json, CLI can override them
    config = load_config("config.json")
    parser.set_defaults(pipeline=config["pipeline"], forwarding=config["forwarding"])

    args = parser.parse_args()

    print(f"Pipeline:   {'ON' if args.pipeline else 'OFF'}")
    print(f"Forwarding: {'ON' if args.forwarding else 'OFF'}")

    # Pass args to simulator
    # simulator = Simulator(args.assembly_file, args.pipeline, args.forwarding, config)
    # simulator.run()

if __name__ == "__main__":
    main()