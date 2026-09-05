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

# Bijgewerkte query met FilterInputDtoInput en de geneste 'event' structuur
GRAPHQL_QUERY = """
query GET_EVENT_LISTINGS($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
  eventListings(filters: $filters, pageSize: $pageSize, page: $page) {
    data {
      id
      event {
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
    }
    totalResults
  }
}
"""

def fetch_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "filters": {
                "areas": {"eq": 32},
                "listingDate": {
                    "gte": f"{today_date}T00:00:00.000Z",
                    "lte": f"{today_date}T23:59:59.999Z"
                }
            },
            "pageSize": 100,
            "page": 1
        }
    }

    response = requests.post(URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        res_json = response.json()
        
        if "errors" in res_json:
            print("GraphQL Fouten:", res_json["errors"])
            raise Exception("GraphQL query is afgewezen door RA.")

        listings = res_json.get("data", {}).get("eventListings", {}).get("data", [])
        
        # Uitpakken van de geneste event-objects voor de front-end
        events = [item["event"] for item in listings if item.get("event")]
        
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
