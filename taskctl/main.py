import argparse
import sys

from .commands import cmd_create, cmd_list


def main():
    parser = argparse.ArgumentParser(prog="taskctl", description="A minimal task manager")
    subparsers = parser.add_subparsers(dest="command")

    # taskctl create
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("-t", "--title", default=None, help="Task title")
    create_parser.add_argument("-d", "--description", default=None, help="Task description")
    create_parser.add_argument("-e", "--eta", default=None, help="ETA (e.g. 30m, 1h, 1d)")
    create_parser.add_argument("-s", "--start", action="store_true", help="Start the task immediately")

    # taskctl list
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("-d", "--duration", default=None, help="Duration to look back (e.g. 7d, 24h)")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(
            title=args.title,
            description=args.description,
            eta=args.eta,
            start=args.start,
        )
    elif args.command == "list":
        cmd_list(duration=args.duration)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
