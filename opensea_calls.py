import requests
import json
from config import OPENSEA_API_KEY

def get_collection(contract):
    """Returns collection info given a contract address"""
    url = f"https://api.opensea.io/api/v1/asset/{contract}/1/?include_orders=false"
    headers = {"X-API-KEY": OPENSEA_API_KEY}
    response = requests.get(url, headers=headers)
    collection = json.loads(response.text)
    return collection
   
    
def get_collection_stats(slug):
    url = f"https://api.opensea.io/api/v1/collection/{slug}/stats"

    headers = {
        "Accept": "application/json",
        "X-API-KEY": OPENSEA_API_KEY
    }

    response = requests.get(url, headers=headers)
    stats = json.loads(response.text)['stats']
    print(stats)
    print(type(stats))
    return stats


def get_opensea_events(token_id, contract, slug, only_opensea=True):
    """Returns a dict of successful sales on Opensea"""
    url = f"https://api.opensea.io/api/v1/events?only_opensea={only_opensea}&token_id={token_id}&asset_contract_address={contract}&collection_slug={slug}&event_type=successful"

    headers = {
        "Accept": "application/json",
        "X-API-KEY": OPENSEA_API_KEY
    }

    response = requests.get(url, headers=headers)
    try:
        events = json.loads(response.text)['asset_events']
    except:
        events = None
    # print("-"*25, "\n")
    # print(f"Events for {slug} #{token_id}:")
    print(events, "\n")
    return events
    
    
def get_collection_slug(contract):
    return get_collection(contract)['collection']['slug']