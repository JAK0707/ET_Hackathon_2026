from __future__ import annotations

from datetime import datetime

import requests
from bs4 import BeautifulSoup


class FlowService:
    def fetch_flow_snapshot(self) -> dict[str, str | float]:
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table")
            if not table:
                raise ValueError("No FII/DII table found")
            rows = table.find_all("tr")
            latest = [cell.get_text(strip=True) for cell in rows[1].find_all(["td", "th"])]
            return {
                "date": latest[0],
                "fii_net_cr": float(latest[-2].replace(",", "")),
                "dii_net_cr": float(latest[-1].replace(",", "")),
                "source": url,
            }
        except Exception:
            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "fii_net_cr": 1250.0,
                "dii_net_cr": -410.0,
                "source": "fallback-demo-snapshot",
            }
