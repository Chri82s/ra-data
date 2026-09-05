import json
import os
import requests
from datetime import datetime, timezone

URL = "https://ra.co/graphql"

# Uitgebreide headers om te lijken op een echte browser-sessie
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://ra.co/events/nl/all",
    "Origin": "https://ra.co",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not=A?Brand";v="24", "Google Chrome";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

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
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "indicesFilter": {
                "area": 32,
                "dateFrom": f"{today_date}T00:00:00.000Z",
                "dateTo": f"{today_date}T23:59:59.999Z"
            },
            "pageSize": 100,
            "page": 1
        }
    }

    session = requests.Session()
    
    # Eerst de hoofdpagina bezoeken om eventuele cookies op te halen
    try:
        session.get("https://ra.co/events/nl/all", headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"Waarschuwing bij ophalen cookies: {e}")

    response = session.post(URL, json=payload, headers=HEADERS, timeout=15)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            res_json = response.json()
        except Exception:
            print("Antwoord was geen geldige JSON. Mogelijke Cloudflare block.")
            print(response.text[:500])
            raise Exception("Geen geldige JSON ontvangen.")
            
        if "errors" in res_json:
            print("GraphQL Errors:", res_json["errors"])
            raise Exception("GraphQL query is afgewezen door RA.")

        events = res_json.get("data", {}).get("eventListing", {}).get("data", [])
        
        os.makedirs("data", exist_ok=True)
        output_file = f"data/events_nl_{today_date}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
            
        print(f"Succesvol {len(events)} evenementen opgeslagen in {output_file}")
    else:
        print(f"HTTP Fout code: {response.status_code}")
        print("Response body preview:", response.text[:300])
        raise Exception(f"HTTP request mislukt met code {response.status_code}")

if __name__ == "__main__":
    fetch_events()
