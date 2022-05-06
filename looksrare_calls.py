import requests
import json

def get_looksrare_events(contract, token_id):
    """Returns a dict of successful sales on Looksrare"""
    url = f"https://api.looksrare.org/api/v1/events?collection={contract}&tokenId={token_id}&type=SALE&first=10&cursor=192921"

    response = requests.get(url)
    events = json.loads(response.text)['data'][0]
    return events