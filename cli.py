import argparse

from settings import SETTINGS_PATH

CONFIG_PATH = "config.yaml"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search equi-score starter lists for configured riders and horses.",
    )
    parser.add_argument(
        "--config",
        default=CONFIG_PATH,
        help=f"Search config YAML (default: {CONFIG_PATH})",
    )
    parser.add_argument(
        "--settings",
        default=SETTINGS_PATH,
        help=f"Technical settings JSON (default: {SETTINGS_PATH})",
    )
    parser.add_argument(
        "--output",
        help="Result JSON path (overrides settings.json output)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cached HTTP responses; still writes fresh responses to .cache/",
    )
    return parser.parse_args(argv)
