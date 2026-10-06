"""Regression cases for binding a batching solution to its supplied instance."""
import unittest
from batching_problem.definitions import Article, Batch, Instance, Order, Parameters, WarehouseItem


class InputBinding(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.a = Article('a', 1)
        self.b = Article('b', 2)
        self.wa = WarehouseItem('item-a', 10, 1, self.a, 'zone-0')
        self.wb = WarehouseItem('item-b', 20, 2, self.b, 'zone-0')
        self.oa = Order('order-a', [self.a])
        self.ob = Order('order-b', [self.b])
        self.instance.articles = [self.a, self.b]
        self.instance.warehouse_items = [self.wa, self.wb]
        self.instance.orders = [self.oa, self.ob]
        self.instance.zones = ['zone-0']
        self.instance.parameters = Parameters(
            min_number_requested_items=1, max_orders_per_batch=1,
            max_container_volume=3, first_row=-50, last_row=50,
            first_aisle=-50, last_aisle=50)

    def feasible(self, order, item):
        self.instance.batches = [Batch([order], [[item]])]
        return self.instance.check_feasibility()

    def test_original_objects_are_accepted(self):
        self.assertTrue(self.feasible(self.oa, self.wa))

    def test_equivalent_reconstructed_objects_are_accepted(self):
        article = Article('a', 1)
        order = Order('order-a', [article])
        item = WarehouseItem('item-a', 10, 1, article, 'zone-0')
        self.assertTrue(self.feasible(order, item))

    def test_changed_item_coordinates_are_rejected(self):
        item = WarehouseItem('item-a', 1, 1, self.a, 'zone-0')
        self.assertEqual(self.instance.picklist_cost([self.wa]), 22)
        self.assertEqual(self.instance.picklist_cost([item]), 4)
        self.assertFalse(self.feasible(self.oa, item))

    def test_changed_item_zone_is_rejected(self):
        item = WarehouseItem('item-a', 10, 1, self.a, 'zone-other')
        self.assertFalse(self.feasible(self.oa, item))

    def test_changed_item_article_is_rejected(self):
        item = WarehouseItem('item-a', 10, 1, self.b, 'zone-0')
        self.assertFalse(self.feasible(self.ob, item))

    def test_changed_item_volume_is_rejected(self):
        item = WarehouseItem('item-a', 10, 1, Article('a', .1), 'zone-0')
        self.assertFalse(self.feasible(self.oa, item))

    def test_order_absent_from_input_is_rejected(self):
        self.assertFalse(self.feasible(Order('order-absent', [self.a]), self.wa))

    def test_changed_input_order_articles_are_rejected(self):
        self.assertFalse(self.feasible(Order('order-a', [self.b]), self.wb))

    def test_changed_input_order_multiplicity_is_rejected(self):
        self.instance.orders = [Order('order-a', [self.a, self.a])]
        self.assertFalse(self.feasible(self.oa, self.wa))


if __name__ == '__main__':
    unittest.main()
