import json
import os
import requests
from datetime import datetime, timedelta, timezone

URL = "https://ra.co/graphql"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": "https://ra.co/events/nl/all",
    "Origin": "https://ra.co"
}

GRAPHQL_QUERY = """
query GET_EVENT_LISTINGS($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
  eventListings(filters: $filters, pageSize: $pageSize, page: $page) {
    totalResults
    data {
      id
      event {
        id
        title
        date
        startTime
        endTime
        contentUrl
        flyerFront
        attending
        venue {
          id
          name
          contentUrl
        }
        artists {
          id
          name
        }
      }
    }
  }
}
"""

def fetch_events():
    now = datetime.now(timezone.utc)
    today_date = now.strftime('%Y-%m-%d')
    next_week = (now + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Probeer verschillende bekende RA-filtervariaties voor Nederland (Area 32)
    filter_attempts = [
        # Variatie 1: area (enkelvoud) met datum
        {
            "area": {"eq": 32},
            "listingDate": {
                "gte": f"{today_date}T00:00:00.000Z",
                "lte": f"{next_week}T23:59:59.999Z"
            }
        },
        # Variatie 2: areas (meervoud in array)
        {
            "areas": {"in": [32]},
            "listingDate": {
                "gte": f"{today_date}T00:00:00.000Z",
                "lte": f"{next_week}T23:59:59.999Z"
            }
        },
        # Variatie 3: Alleen area filter
        {
            "areas": {"eq": 32}
        }
    ]

    items = []
    total = 0

    for idx, filters in enumerate(filter_attempts, 1):
        payload = {
            "query": GRAPHQL_QUERY,
            "variables": {
                "filters": filters,
                "pageSize": 100,
                "page": 1
            }
        }

        response = requests.post(URL, json=payload, headers=HEADERS)
        if response.status_code == 200:
            res_json = response.json()
            if "errors" not in res_json:
                listing = res_json.get("data", {}).get("eventListings", {})
                total = listing.get("totalResults", 0)
                items = listing.get("data", [])
                
                print(f"Poging {idx}: {total} evenementen gevonden met filter: {list(filters.keys())}")
                if total > 0:
                    break
            else:
                print(f"Poging {idx} gaf GraphQL fout, probeert volgende...")
        else:
            print(f"Poging {idx} mislukt met status {response.status_code}")

    events = []
    for item in items:
        ev = item.get("event")
        if ev:
            ev["flyerUrl"] = ev.get("flyerFront")
            events.append(ev)

    os.makedirs("data", exist_ok=True)
    output_file = f"data/events_nl_{today_date}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
        
    print(f"Totaal {len(events)} evenementen opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_events()
