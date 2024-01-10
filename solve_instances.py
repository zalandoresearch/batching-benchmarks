import random
import time
import logging

from batching_problem.definitions import Instance
from generate_instances import parser
from distance_greedy_algorithm.solver import greedy_solver


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run(args, name) -> None:
    path = f"{args.dir}/{name}"
    logger.info(f"Running algorithm for {name} instance")
    start_time = time.time()
    logger.info("Reading instance")
    instance = Instance()
    instance.read(path)
    logger.info("Creating batches")
    instance.batches = greedy_solver(instance, choose_random_order=args.algo == "rdga")
    logger.info("batches created")
    time_elapsed = round(time.time() - start_time)
    logger.info("Evaluating results")
    instance.evaluate(time_elapsed)
    logger.info("writing results")
    instance.store_result(path)
    logger.info(f"Results for {name} computed and stored.")


if __name__ == "__main__":
    parser.add_argument(
        "-a",
        "--algo",
        help="Specify algorithm: Distance Greedy Algorithm (dga) or Randomized DGA (rdga)",
        default="dga",
        choices=["dga", "rdga"],
    )

    random.seed(1)
    args = parser.parse_args()

    for size in args.instance_types:
        for nbr in range(args.nbr_instances):
            run(args, f"{size}-{nbr}")
