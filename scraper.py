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
    
    # ISO timestamps zoals RA ze verwacht in listingDate filters
    start_iso = f"{today_date}T00:00:00.000Z"
    end_iso = f"{today_date}T23:59:59.999Z"

    # Poging 1: Vandaag ophalen met ISO timestamps
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "filters": {
                "areas": {"eq": 32},
                "listingDate": {
                    "gte": start_iso,
                    "lte": end_iso
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
            print("GraphQL Fouten van RA:", res_json["errors"])
            raise Exception("GraphQL query is afgewezen door RA.")

        listing = res_json.get("data", {}).get("eventListings", {})
        total = listing.get("totalResults", 0)
        items = listing.get("data", [])

        # Fallback: Als 0 resultaten voor exact vandaag, vraag de komende 7 dagen op
        if total == 0:
            print("0 resultaten voor vandaag. Proberen met een ruimere datumbereik (komende 7 dagen)...")
            next_week_iso = (now + timedelta(days=7)).strftime('%Y-%m-%dT23:59:59.999Z')
            payload["variables"]["filters"]["listingDate"]["lte"] = next_week_iso
            
            response = requests.post(URL, json=payload, headers=HEADERS)
            if response.status_code == 200:
                res_json = response.json()
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
            
        print(f"Succesvol {len(events)} evenementen opgeslagen in {output_file}")
    else:
        print(f"HTTP Fout code: {response.status_code}")
        raise Exception(f"HTTP request mislukt met code {response.status_code}")

if __name__ == "__main__":
    fetch_events()
