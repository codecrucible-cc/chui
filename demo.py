#!/usr/bin/env python3
"""
Demo script showing Chui framework features
"""
from chui.cli import ChuiCLI

def main():
    try:
        cli = ChuiCLI()
        cli.debug = True  # Enable debug output
        cli.onecmd("playground")

    except Exception as e:
        print(f"Error starting CLI: {str(e)}")
        raise

if __name__ == "__main__":
    main()
