import json
import os
import requests
from datetime import datetime, timezone

URL = "https://ra.co/graphql"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": "https://ra.co/events/nl/all"
}

# Uitgebreide GraphQL query met expliciet datumfilter
GRAPHQL_QUERY = """
query GET_DEFAULT_EVENTS_LISTING($indicesFilter: IndicesFilterInput, $pageSize: Int, $page: Int) {
  eventListing(indicesFilter: $indicesFilter, pageSize: $pageSize, page: $page) {
    data {
      id
      title
      date
      startTime
      endTime
      contentUrl
      flyerUrl
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
    totalResults
  }
}
"""

def fetch_events():
    today_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "indicesFilter": {
                "area": 32,
                "dateFrom": f"{today_iso}T00:00:00.000Z"
            },
            "pageSize": 50,
            "page": 1
        }
    }

    response = requests.post(URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        res_json = response.json()
        events = res_json.get("data", {}).get("eventListing", {}).get("data", [])
        
        os.makedirs("data", exist_ok=True)
        output_file = f"data/events_nl_{today_iso}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
            
        print(f"Succesvol {len(events)} evenementen opgeslagen in {output_file}")
    else:
        print(f"Fout bij ophalen data: HTTP {response.status_code}")

if __name__ == "__main__":
    fetch_events()
