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
    tomorrow_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # We vragen de events van vandaag op tot morgen
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "filters": {
                "areas": {"eq": 32},
                "listingDate": {
                    "gte": f"{today_date}T00:00:00.000Z",
                    "lte": f"{tomorrow_date}T23:59:59.999Z"
                }
            },
            "pageSize": 100,
            "page": 1
        }
    }

    response = requests.post(URL, json=payload, headers=HEADERS)
    print(f"HTTP Status: {response.status_code}")
    
    if response.status_code == 200:
        res_json = response.json()
        
        if "errors" in res_json:
            print("GraphQL Fouten:", res_json["errors"])
            raise Exception("GraphQL query is afgewezen door RA.")

        listing_data = res_json.get("data", {}).get("eventListings", {})
        total_results = listing_data.get("totalResults", 0)
        items = listing_data.get("data", [])
        
        print(f"Totaal aantal gevonden resultaten volgens RA: {total_results}")
        print(f"Aantal items in deze pagina: {len(items)}")

        events = []
        for item in items:
            ev = item.get("event")
            if ev:
                ev["flyerUrl"] = ev.get("flyerFront")
                events.append(ev)
        
        # Als er geen events zijn gefilterd via item['event'], bewaar het originele item
        if not events and items:
            events = items

        os.makedirs("data", exist_ok=True)
        output_file = f"data/events_nl_{today_date}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
            
        print(f"Succesvol {len(events)} evenementen opgeslagen in {output_file}")
    else:
        print(f"HTTP Fout code: {response.status_code}")
        raise Exception(f"HTTP request mislukt met code {response.status_code}")

if __name__ == "__main__":
    fetch_events()
