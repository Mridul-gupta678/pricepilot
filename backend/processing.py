import re
from typing import Optional

class DataProcessor:
    @staticmethod
    def normalize_price(price_str) -> Optional[float]:
        """
        Converts price string (e.g., 'Rs. 1,299', '$12.99') to float.
        Returns None if conversion fails.
        """
        if price_str is None or price_str in ["Unavailable", "Sold Out"]:
            return None
        if isinstance(price_str, (int, float)):
            try:
                return float(price_str)
            except ValueError:
                return None
        s = str(price_str)
        clean_str = s.replace(',', '')
        match = re.search(r'\d+(\.\d+)?', clean_str)
        if not match:
            return None
        try:
            return float(match.group())
        except ValueError:
            return None

    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Cleans and normalizes product title.
        """
        if not title:
            return "Unknown Product"
        return " ".join(title.split())

    @staticmethod
    def calculate_deal_score(current_price: float, history_avg: float) -> dict:
        """
        Calculates a deal score (0-10) and label.
        """
        if not history_avg or history_avg == 0:
            return {"score": 5, "label": "Fair Price", "savings": 0}
            
        savings_pct = ((history_avg - current_price) / history_avg) * 100
        
        if savings_pct >= 20:
            return {"score": 10, "label": "Great Deal", "savings": savings_pct}
        elif savings_pct >= 10:
            return {"score": 8, "label": "Good Deal", "savings": savings_pct}
        elif savings_pct >= -5:
            return {"score": 6, "label": "Fair Price", "savings": savings_pct}
        else:
            return {"score": 3, "label": "Overpriced", "savings": savings_pct}
