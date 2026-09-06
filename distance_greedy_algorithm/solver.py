from typing import Set, Dict, List
from collections import defaultdict
import random
import logging

from batching_problem.definitions import Batch, Instance, WarehouseItem, Order, Article

logger = logging.getLogger(__name__)


def compute_picklists(
    items: List[WarehouseItem], max_container_volume: int
) -> List[List[WarehouseItem]]:
    items_by_zone = defaultdict(list)
    for item in items:
        items_by_zone[item.zone].append(item)

    picklists = []
    for zone in items_by_zone:
        picklist = []
        cur_volume = 0
        for item in sorted(items_by_zone[zone], key=lambda i: (i.aisle, i.row)):
            if cur_volume + item.article.volume <= max_container_volume:
                picklist.append(item)
                cur_volume += item.article.volume
            else:
                picklists.append(picklist)
                picklist = [item]
                cur_volume = item.article.volume
        if len(picklist) > 0:
            picklists.append(picklist)
    return picklists


def find_best_order(
    remaining_orders: List[Order],
    selected_items: List[WarehouseItem],
    warehouse_items: Dict[Article, Set[WarehouseItem]],
    instance: Instance,
) -> (float, List[WarehouseItem], Order):
    selected_items_by_zone = {
        zone: [WarehouseItem("conveyor", 0, 0, None, zone)] for zone in instance.zones
    }
    for i in selected_items:
        selected_items_by_zone[i.zone].append(i)

    def distance_per_item(order: Order) -> (float, List[WarehouseItem]):
        total_distance = 0
        add_items = set()
        add_items_by_zone = defaultdict(list)
        for article in order.positions:
            distance, item = min(
                (
                    min(
                        instance.distance(item1, item2)
                        for item2 in selected_items_by_zone[item1.zone]
                        + add_items_by_zone[item1.zone]
                    ),
                    item1,
                )
                for item1 in warehouse_items[article]
                if item1 not in add_items
            )
            total_distance += distance
            add_items_by_zone[item.zone].append(item)
            add_items.add(item)
        return total_distance / len(add_items), sorted(add_items, key=lambda i: i.id)

    # `remaining_orders` is iterated in a fixed order (a list, see greedy_solver)
    # and ties are broken on the average distance deterministically, so the
    # result does not depend on any set iteration order.
    return min(
        ((*distance_per_item(order), order) for order in remaining_orders),
        key=lambda candidate: candidate[0],
    )


def greedy_solver(instance: Instance, k: int = None) -> List[Batch]:
    item_goal = instance.parameters.min_number_requested_items
    # A list (not a set) so the iteration/selection order is deterministic
    # without per-step sorting.
    remaining_orders = list(instance.orders)

    warehouse_article_items: Dict[Article, Set[WarehouseItem]] = defaultdict(set)
    for item in instance.warehouse_items:
        warehouse_article_items[item.article].add(item)

    batches = []

    # repeat while item goal is not reached and there are remaining orders in the pool
    while item_goal > 0 and len(remaining_orders) > 0:
        logger.info(f"Remaining items to batch: {item_goal}")
        batch_orders = []
        batch_selected_items = []
        logger.info(
            f"Creating a batch, total remaining orders in the pool: {len(remaining_orders)}"
        )
        # Stop the batch when it is full, the pool is empty, or the (remaining)
        # item goal has been reached. The last condition matches Algorithm 1 and
        # keeps the batch from overshooting the item goal.
        while (
            len(remaining_orders) > 0
            and len(batch_orders) < instance.parameters.max_orders_per_batch
            and len(batch_selected_items) < item_goal
        ):
            # distinguishing between DGA and RDGA
            if k is not None:
                # sample min(k, pool size) orders uniformly at random, without
                # replacement; the caller's random.seed makes this reproducible
                sample_idxs = random.sample(
                    range(len(remaining_orders)), min(k, len(remaining_orders))
                )
                candidate_orders = [remaining_orders[i] for i in sample_idxs]
            else:
                candidate_orders = remaining_orders
            cost, selected_items, selected_order = find_best_order(
                candidate_orders, batch_selected_items, warehouse_article_items, instance
            )
            if selected_order is None:
                break
            batch_orders.append(selected_order)
            batch_selected_items.extend(selected_items)
            for item in selected_items:
                warehouse_article_items[item.article].remove(item)
            if k is not None:
                # O(1) removal: swap the picked order with the last and pop
                idx = sample_idxs[candidate_orders.index(selected_order)]
                remaining_orders[idx] = remaining_orders[-1]
                remaining_orders.pop()
            else:
                remaining_orders.remove(selected_order)

        batch = Batch(
            batch_orders,
            compute_picklists(
                batch_selected_items, instance.parameters.max_container_volume
            ),
        )
        batches.append(batch)
        logger.info(f"Batch created with a total of {len(batch_selected_items)} items")

        item_goal -= len(batch_selected_items)

    return batches
