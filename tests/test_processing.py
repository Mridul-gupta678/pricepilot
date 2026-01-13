import unittest
from backend.processing import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def test_normalize_price_valid(self):
        self.assertEqual(DataProcessor.normalize_price("Rs. 1,299"), 1299.0)
        self.assertEqual(DataProcessor.normalize_price("$12.99"), 12.99)
        self.assertEqual(DataProcessor.normalize_price("1500"), 1500.0)

    def test_normalize_price_invalid(self):
        self.assertIsNone(DataProcessor.normalize_price("Unavailable"))
        self.assertIsNone(DataProcessor.normalize_price("Sold Out"))
        self.assertIsNone(DataProcessor.normalize_price(""))

    def test_calculate_deal_score(self):
        # 100 vs 120 (avg) -> 20/120 savings = ~16% -> Good Deal
        score = DataProcessor.calculate_deal_score(100, 120)
        self.assertEqual(score["label"], "Good Deal")
        
        # 100 vs 100 (avg) -> 0% savings -> Fair Price
        score = DataProcessor.calculate_deal_score(100, 100)
        self.assertEqual(score["label"], "Fair Price")
        
        # 150 vs 100 (avg) -> -50% savings -> Overpriced
        score = DataProcessor.calculate_deal_score(150, 100)
        self.assertEqual(score["label"], "Overpriced")

if __name__ == '__main__':
    unittest.main()
