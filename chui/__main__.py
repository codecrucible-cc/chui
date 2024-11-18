# chui/__main__.py

import sys
import argparse
from typing import List, Optional
from pathlib import Path
from .cli import ChuiCLI
from chui.core.create_plugin import PluginCreator


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        description="Chui Framework CLI",
        usage="""python -m chui <command> [<args>]

Commands:
   create_plugin     Create a new plugin
   shell            Launch interactive shell (default if no command given)
   help             Show this help message
""")

    parser.add_argument('command', help='Command to run', nargs='?', default='shell')

    return parser


def create_plugin_subcommand(args: List[str]) -> int:
    """Handle create_plugin subcommand"""
    # Create subparser for create_plugin command
    parser = argparse.ArgumentParser(
        description="Create a new Chui plugin",
        prog='python -m chui create_plugin'
    )
    parser.add_argument(
        'name',
        help="Name of the plugin to create"
    )
    parser.add_argument(
        '--description', '-d',
        default="A plugin for the Chui framework",
        help="Plugin description"
    )
    parser.add_argument(
        '--author', '-a',
        default="",
        help="Plugin author name"
    )

    try:
        # Parse create_plugin specific args
        plugin_args = parser.parse_args(args)

        # Create the plugin
        creator = PluginCreator()
        plugin_dir = creator.create(
            name=plugin_args.name,
            description=plugin_args.description,
            author=plugin_args.author
        )

        # Show success message
        print(f"\nSuccessfully created plugin: {plugin_args.name}")
        print(f"Location: {plugin_dir}")
        print("\nNext steps:")
        print(f"1. Add your plugin code to {plugin_dir}")
        print("2. Enable the plugin in Chui's configuration:")
        print(f"   python -m chui shell")
        print(f"   chui> settings set plugins.enabled [\"{plugin_args.name}\"]")
        print(f"3. Run the tests: pytest {plugin_dir}/test_plugin.py")
        print("\nFor more information, see the README.md in your plugin directory")

        return 0

    except Exception as e:
        print(f"Error creating plugin: {str(e)}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for the chui command"""
    parser = create_parser()

    # Parse just the command first
    args = parser.parse_args(sys.argv[1:2])

    # If no command is specified, default to shell
    if not args.command:
        args.command = 'shell'

    # Handle different commands
    if args.command == 'help':
        parser.print_help()
        return 0

    elif args.command == 'create_plugin':
        # Pass remaining arguments to create_plugin command
        return create_plugin_subcommand(sys.argv[2:])

    elif args.command == 'shell':
        # Launch interactive shell
        cli = ChuiCLI()
        try:
            cli.cmdloop()
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            print(f"Error in CLI: {str(e)}", file=sys.stderr)
            return 1

    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())