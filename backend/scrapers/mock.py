import random
import time
from .base import BaseScraper
from typing import Dict, Any

class MockScraper(BaseScraper):
    def fetch_product(self, url: str) -> Dict[str, Any]:
        # Simulate network delay
        time.sleep(0.5)
        
        # Deterministic mock data based on URL length to simulate variety
        seed = len(url)
        random.seed(seed)
        
        titles = [
            "Mock Premium Wireless Headphones",
            "Mock Smart Watch Series 5",
            "Mock Running Shoes Pro",
            "Mock Gaming Laptop 15-inch"
        ]
        
        base_price = random.randint(1000, 50000)
        
        return {
            "title": random.choice(titles),
            "price": str(base_price),
            "image": "https://via.placeholder.com/300",
            "source": "Mock Data Feed"
        }
