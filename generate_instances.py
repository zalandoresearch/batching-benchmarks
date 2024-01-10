import random as r
import os
import logging
import argparse

from batching_problem.generator import generate_instance

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

parameters = {
    "small": {
        "nbr_warehouse_items": 10_000,
        "nbr_orders": 500,
        "nbr_zones": 10,
    },
    "medium": {
        "nbr_warehouse_items": 100_000,
        "nbr_orders": 5_000,
        "nbr_zones": 50,
    },
    "large": {
        "nbr_warehouse_items": 1_000_000,
        "nbr_orders": 50_000,
        "nbr_zones": 100,
    },
}

parser = argparse.ArgumentParser()
parser.add_argument(
    "-n",
    "--nbr_instances",
    type=int,
    help="Number of instances per type",
    default=5,
)
parser.add_argument(
    "-t",
    "--instance-types",
    type=str,
    help="Directory for writing instances",
    nargs="+",
    default=parameters.keys(),
    choices=parameters.keys(),
)
parser.add_argument(
    "-d",
    "--dir",
    type=str,
    help="Directory for writing instances",
    default="instances",
)


if __name__ == "__main__":
    args = parser.parse_args()
    r.seed(1)
    os.system(f"mkdir -p {args.dir}")
    for size in args.instance_types:
        for nbr in range(args.nbr_instances):
            path = f"{args.dir}/{size}-{nbr}"
            os.system(f"mkdir -p {path}")
            generate_instance(path, parameters[size])
