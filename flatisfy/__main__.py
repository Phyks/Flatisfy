# coding: utf-8
"""
Main entry point of the Flatisfy code.
"""
from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
import sys

logging.basicConfig()

# pylint: disable=locally-disabled,wrong-import-position
import flatisfy.config
from flatisfy import cmds
from flatisfy import data
from flatisfy import fetch
from flatisfy import tools
from flatisfy import tests

# pylint: enable=locally-disabled,wrong-import-position


LOGGER = logging.getLogger("flatisfy")


def parse_args(argv=None):
    """
    Create parser and parse arguments.
    """
    parser = argparse.ArgumentParser(
        prog="Flatisfy", description="Find the perfect flat."
    )

    # Parent parser containing arguments common to any subcommand
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--data-dir", help="Location of Flatisfy data directory."
    )
    parent_parser.add_argument("--config", help="Configuration file to use.")
    parent_parser.add_argument(
        "--passes",
        choices=[0, 1, 2, 3],
        type=int,
        help="Number of passes to do on the filtered data.",
    )
    parent_parser.add_argument(
        "--max-entries", type=int, help="Maximum number of entries to fetch."
    )
    parent_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging output."
    )
    parent_parser.add_argument("-vv", action="store_true", help="Debug logging output.")
    parent_parser.add_argument(
        "--constraints",
        type=str,
        help="Comma-separated list of constraints to consider.",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="cmd", help="Available subcommands")

    # Build data subcommand
    subparsers.add_parser(
        "build-data", parents=[parent_parser], help="Build necessary data"
    )

    # Init config subcommand
    parser_init_config = subparsers.add_parser(
        "init-config", parents=[parent_parser], help="Initialize empty configuration."
    )
    parser_init_config.add_argument(
        "output", nargs="?", help="Output config file. Use '-' for stdout."
    )

    # Fetch subcommand parser
    subparsers.add_parser("fetch", parents=[parent_parser], help="Fetch housings posts")

    # Filter subcommand parser
    parser_filter = subparsers.add_parser(
        "filter",
        parents=[parent_parser],
        help="Filter housings posts according to constraints in config.",
    )
    parser_filter.add_argument(
        "--input",
        help=(
            "Optional JSON dump of the housings post to filter. If provided, "
            "no additional fetching of infos is done, and the script outputs "
            "a filtered JSON dump on stdout. If not provided, update status "
            "of the flats in the database."
        ),
    )

    # Import subcommand parser
    import_filter = subparsers.add_parser(
        "import", parents=[parent_parser], help="Import housing posts in database."
    )
    import_filter.add_argument(
        "--new-only",
        action="store_true",
        help=("Download new housing posts only but do not refresh existing ones"),
    )

    # Purge subcommand parser
    subparsers.add_parser("purge", parents=[parent_parser], help="Purge database.")

    # Serve subcommand parser
    parser_serve = subparsers.add_parser(
        "serve", parents=[parent_parser], help="Serve the web app."
    )
    parser_serve.add_argument("--port", type=int, help="Port to bind to.")
    parser_serve.add_argument("--host", help="Host to listen on.")

    # Test subcommand parser
    subparsers.add_parser("test", parents=[parent_parser], help="Unit testing.")

    return parser.parse_args(argv)


def main():
    """
    Main module code.
    """
    # pylint: disable=locally-disabled,too-many-branches
    # Parse arguments
    args = parse_args()

    # Set logger
    if args.vv:
        logging.getLogger("").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger("").setLevel(logging.INFO)
        # sqlalchemy INFO level is way too loud, just stick with WARNING
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    else:
        logging.getLogger("").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Init-config command
    if args.cmd == "init-config":
        flatisfy.config.init_config(args.output)
        sys.exit(0)
    else:
        # Load config
        if args.cmd == "build-data":
            # Data not yet built, do not use it in config checks
            config = flatisfy.config.load_config(args, check_with_data=False)
        else:
            config = flatisfy.config.load_config(args, check_with_data=True)
        if config is None:
            LOGGER.error(
                "Invalid configuration. Exiting. "
                "Run init-config before if this is the first time "
                "you run Flatisfy."
            )
            sys.exit(1)

    # Purge command
    if args.cmd == "purge":
        cmds.purge_db(config)
        return

    # Build data files command
    if args.cmd == "build-data":
        data.preprocess_data(config, force=True)
        return
    # Fetch command
    if args.cmd == "fetch":
        # Fetch and filter flats list
        fetched_flats = fetch.fetch_flats(config)
        fetched_flats = cmds.filter_fetched_flats(
            config, fetched_flats=fetched_flats, fetch_details=True
        )
        # Sort by cost
        fetched_flats = {
            k: tools.sort_list_of_dicts_by(v["new"], "cost")
            for k, v in fetched_flats.items()
        }

        print(tools.pretty_json(fetched_flats))
        return
    # Filter command
    elif args.cmd == "filter":
        # Load and filter flats list
        if args.input:
            fetched_flats = fetch.load_flats_from_file(args.input, config)

            fetched_flats = cmds.filter_fetched_flats(
                config, fetched_flats=fetched_flats, fetch_details=False
            )

            # Sort by cost
            fetched_flats = {
                k: tools.sort_list_of_dicts_by(v["new"], "cost")
                for k, v in fetched_flats.items()
            }

            # Output to stdout
            print(tools.pretty_json(fetched_flats))
        else:
            cmds.import_and_filter(config, load_from_db=True)
        return
    # Import command
    elif args.cmd == "import":
        cmds.import_and_filter(config, load_from_db=False, new_only=args.new_only)
        return
    # Serve command
    elif args.cmd == "serve":
        cmds.serve(config)
        return
    # Tests command
    elif args.cmd == "test":
        tests.run()
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
