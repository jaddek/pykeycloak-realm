import argparse
import logging

from pykeycloak_realm.builder import export
from pykeycloak_realm.config import RealmBuilderConfig


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a Keycloak realm from a template to a JSON file."
    )
    parser.add_argument(
        "--from-realm",
        required=True,
        help="Name of the preset config, e.g. 'otago'. Looks for ./data/realms/templates/{name}.realm.yml",
    )
    parser.add_argument(
        "--to-realm",
        required=True,
        help="Name for the output realm file, e.g. 'otago'. Will create ./data/realms/export/{name}.realm.json",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: %(name)s ---> %(asctime)s ====  %(message)s",
    )

    export(
        from_template=args.from_realm,
        to_file=args.to_realm,
        config=RealmBuilderConfig(),
    )


if __name__ == "__main__":
    main()
