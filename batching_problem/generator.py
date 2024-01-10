import random as r
import logging

from batching_problem.definitions import (
    Article,
    WarehouseItem,
    Instance,
    Parameters,
    Order,
)

logger = logging.getLogger(__name__)


def generate_instance(path, parameters):
    nbr_rows = 100
    nbr_aisles = 100

    logger.info(f"Creating instance: {path}")
    instance = Instance()

    assert (
        parameters["nbr_warehouse_items"] >= 2 * parameters["nbr_orders"]
    ), "Specify more warehouse items"

    dist = {2: 100, 3: 50, 4: 20, 5: 5, 6: 2}
    com_items_distribution = [key for key, val in dist.items() for _ in range(val)]

    def nbr_com_items_distribution() -> int:
        return r.choice(com_items_distribution)

    def article_volume() -> float:
        return max(1, round(r.gammavariate(2.0, 20.0)))

    zones = [f"zone-{i}" for i in range(parameters["nbr_zones"])]
    nbr_articles = parameters["nbr_warehouse_items"] // 3
    instance.articles = [
        Article(f"article-{i}", article_volume()) for i in range(nbr_articles)
    ]

    assert (
        nbr_aisles > 3
    ), "Specify more aisles (we have three cross-aisles. no items there)"
    aisles = list(range(1, nbr_aisles // 2)) + [
        -i for i in range(1, (nbr_aisles - 1) // 2)
    ]
    rows = list(range(1, nbr_rows // 2)) + [-i for i in range(1, (nbr_rows - 1) // 2)]

    # Update the instance by adding items, orders and parameters to it
    generate_items(
        aisles, instance, nbr_articles, parameters["nbr_warehouse_items"], rows, zones
    )
    generate_orders(
        dist, instance, nbr_com_items_distribution, parameters["nbr_orders"]
    )
    generate_parameters(instance, nbr_aisles, nbr_rows)

    instance.write(path)
    logger.info(f"Created!")


def generate_parameters(instance, nbr_aisles, nbr_rows):
    nbr_req_items = sum(len(com.positions) for com in instance.orders) // 5
    instance.parameters = Parameters(
        min_number_requested_items=nbr_req_items,
        max_orders_per_batch=50,
        max_container_volume=1000,
        first_row=-(nbr_rows - 1) // 2,
        last_row=nbr_rows // 2,
        first_aisle=-(nbr_aisles - 1) // 2,
        last_aisle=nbr_aisles // 2,
    )


def generate_orders(dist, instance, nbr_com_items_distribution, nbr_orders):
    available_items = [item for item in instance.warehouse_items]
    r.shuffle(available_items)
    instance.orders = []
    for i in range(nbr_orders):
        # we need to ensure at least 2 positions for each order
        cutoff = min(
            max(dist.values()), len(available_items) - 2 * (nbr_orders - i - 1)
        )
        nbr_positions = min(cutoff, nbr_com_items_distribution())

        orders = []
        for _ in range(nbr_positions):
            item = available_items.pop()
            orders.append(item.article)

        instance.orders.append(Order(f"order-{i}", orders))


def generate_items(aisles, instance, nbr_articles, nbr_warehouse_items, rows, zones):
    instance.warehouse_items = []
    for i in range(nbr_warehouse_items):
        row = r.choice(rows)
        aisle = r.choice(aisles)
        zone = r.choice(zones)

        # ensure at least one item of each article
        if i < nbr_articles:
            article = instance.articles[i]
        else:
            article = r.choice(instance.articles)
        instance.warehouse_items.append(
            WarehouseItem(f"warehouse-item-{i}", row, aisle, article, zone)
        )
