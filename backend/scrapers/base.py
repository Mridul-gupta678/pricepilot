from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseScraper(ABC):
    @abstractmethod
    def fetch_product(self, url: str) -> Dict[str, Any]:
        """
        Fetch product details from the given URL.
        Returns a dictionary with keys: title, price, image, source.
        """
        pass

    def fallback(self, reason: str) -> Dict[str, Any]:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Error: {reason}"
        }
