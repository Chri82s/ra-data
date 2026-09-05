import json
import os
import requests
from datetime import datetime, timezone

URL = "https://ra.co/graphql"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": "https://ra.co/events/nl/all",
    "Origin": "https://ra.co"
}

# De werkende GraphQL query voor eventListings
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
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Gebruik de datumindeling YYYY-MM-DD zoals RA het verwacht in de nieuwste frontend
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "filters": {
                "areas": {"eq": 32},
                "listingDate": {
                    "gte": today_date,
                    "lte": today_date
                }
            },
            "pageSize": 100,
            "page": 1
        }
    }

    response = requests.post(URL, json=payload, headers=HEADERS)
    print(f"HTTP Status code: {response.status_code}")
    
    if response.status_code == 200:
        res_json = response.json()
        
        if "errors" in res_json:
            print("GraphQL Fouten ontvangen van RA:", res_json["errors"])
            raise Exception("GraphQL query is afgewezen door RA.")

        listing = res_json.get("data", {}).get("eventListings", {})
        total = listing.get("totalResults", 0)
        items = listing.get("data", [])
        
        print(f"--- RA LOGS ---")
        print(f"Totaal gevonden evenementen volgens RA: {total}")
        print(f"Aantal items opgehaald in deze request: {len(items)}")

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
            
        print(f"Succesvol {len(events)} evenementen verwerkt in {output_file}")
    else:
        print(f"HTTP Fout code: {response.status_code}")
        print("Response:", response.text[:300])
        raise Exception(f"HTTP request mislukt met code {response.status_code}")

if __name__ == "__main__":
    fetch_events()
