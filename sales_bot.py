import json
import time
import json
import decimal
import os
import requests 
from opensea_calls import get_collection_slug, get_opensea_events, get_collection
from looksrare_calls import get_looksrare_events
from twitter_auth import twitter_auth_api_v1, twitter_auth_client_v2
from config import ETHERSCAN_API_KEY, ETHPLORER_API_KEY
from emojis import EMOJIS

def ethereum_price():
    """Gets the current ETH price in USD using Ethplorer API"""
    ethereum = "0x0000000000000000000000000000000000000000"
    ethplorer = requests.get(f'https://api.ethplorer.io/getTokenInfo/{ethereum}?apiKey={ETHPLORER_API_KEY}')
    ethplorer_data = json.loads(ethplorer.text)
    eth_price = decimal.Decimal(ethplorer_data['price']['rate'])

    return eth_price


def get_block_minutes_ago(minutes):
    """Returns the block number for the block mined {minutes} minutes ago using Etherscan API"""    
    seconds = int(time.time())
    tmo = str(seconds - (60 * minutes))
  
    old_block_req = requests.get(f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={tmo}&closest=before&apikey={ETHERSCAN_API_KEY}")
    old_block_data = json.loads(old_block_req.text)
    old_block = old_block_data["result"]
    
    return old_block


def get_tx_info_etherscan(hash):
    request = requests.get(f'https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={hash}&apikey={ETHERSCAN_API_KEY}')
    etherscan_tx_data = json.loads(request.text)['result']
    return etherscan_tx_data


def get_transactions(contract, start_block, end_block=99999999, debug=False):
    """
    Args:
        contract (string): nft contract address
        start_block (int): starting block
        end_block (int, optional): end block. Defaults to 99999999.
        debug (bool, optional): prints info. Defaults to False.

    Returns:
        list: list of dicts of transactions with the contract
    """
    gt = requests.get(f'https://api.etherscan.io/api?module=account&action=tokennfttx&contractaddress={contract}&startblock={start_block}&endblock={end_block}&type=transfer&page=1&sort=desc&apikey={ETHERSCAN_API_KEY}')
    con_data = json.loads(gt.text)

    if con_data["status"] == "0":
        print("No Transactions")
        return 1
    
    else:
        if debug:
            print(con_data["result"])
        return con_data['result']
    

def find_marketplace(transactions):
    print(transactions)
    """Determines which marketplace an NFT was traded on, returns that marketplace name as a string"""    
    ## ['to'] field contains indicator
    gem_xyz_single_contract = "0x0000000035634B55f3D99B071B5A354f48e10BEF".lower()
    gem_swap = "0x83c8f28c26bf6aaca652df1dbbe0e1b56f8baba2".lower()
    opensea_wyvern = "0x7f268357A8c2552623316e2562D90e642bB538E5".lower()
    looksrare_exchange = "0x59728544B08AB483533076417FbBB2fD0B17CE3a".lower()
    
    for hash in transactions:
        
        for token_id in transactions[hash]['token_ids']:
            
            to_address = transactions[hash]['token_ids'][token_id]['transaction_data']['to'].lower()
            print("to_address = ", to_address, type(to_address))
            
            if to_address == gem_xyz_single_contract or to_address == gem_swap:
                transactions[hash]['marketplace'] = "Gem.xyz"
            elif to_address == opensea_wyvern:
                transactions[hash]['marketplace'] = "OpenSea"
                print("opensea")
            elif to_address == looksrare_exchange:
                transactions[hash]['marketplace'] = "LooksRare"
                
                
def get_marketplace_link(marketplace, contract, token_id):
    links = {
        "OpenSea":f"https://opensea.io/assets/{contract}/{token_id}",
        "LooksRare":f"https://looksrare.org/collections/{contract}/{token_id}#activity",
        "Gem.xyz":None,
    }
    return links[marketplace] if marketplace in links else None
    

def create_txn_dict(txns):
    """Creates a dict of transaction hashes with tx data and marketplace

    Args:
        transactions (list): transactions from the get_transactions function
    """
    transactions = {}
    for i in range(len(txns)):
        hash = txns[i]['hash']
        token_id = int(txns[i]['tokenID'])
        
        if hash not in transactions:
            transactions[hash] = {}
            transactions[hash]['token_ids'] = {}
            transactions[hash]['token_ids'][token_id] = {}
            
            transactions[hash]['token_ids'][token_id]['etherscan_data'] = txns[i]
            transactions[hash]['token_ids'][token_id]['transaction_data'] = get_tx_info_etherscan(hash)
            transactions[hash]['token_ids'][token_id]['slug'] = get_collection_slug(transactions[hash]['token_ids'][token_id]['etherscan_data']['contractAddress'])
            transactions[hash]['token_ids'][token_id]['marketplace_event'] = None
            
            # hash level dict keys:
            transactions[hash]['marketplace'] = None
            try:
                transactions[hash]['value'] = int(transactions[hash]['token_ids'][token_id]['transaction_data']['value'], 16)
            except:
                transactions[hash]['value'] = None
                
        else:
            transactions[hash]['token_ids'][token_id] = {}
            transactions[hash]['token_ids'][token_id]['etherscan_data'] = txns[i]
            transactions[hash]['token_ids'][token_id]['transaction_data'] = get_tx_info_etherscan(hash)    
    
    # Determine which marketplace it came from
    find_marketplace(transactions)
        
    return transactions


def get_marketplace_event(transactions):
    """Gets the most recent marketplace event for each nft in the hash dict

    Args:
        transactions (dict): dict of txns from the create_txn_dict function
    """
    for hash in transactions:
        marketplace = transactions[hash]['marketplace']
        
        if marketplace == 'OpenSea':
            for nft_id in transactions[hash]['token_ids']:
                transactions[hash]['token_ids'][nft_id]['marketplace_event'] = get_opensea_events(nft_id, transactions[hash]['token_ids'][nft_id]['etherscan_data']['contractAddress'], transactions[hash]['token_ids'][nft_id]['slug'])[0]
       
        elif marketplace == 'LooksRare':
            for nft_id in transactions[hash]['token_ids']:
                transactions[hash]['token_ids'][nft_id]['marketplace_event'] = get_looksrare_events(transactions[hash]['token_ids'][nft_id]['etherscan_data']['contractAddress'], nft_id)
        
        elif marketplace == 'Gem.xyz':
            pass 
        
        
def save_image_file(token_id, img_url):
    with open(f'{token_id}.png', 'wb') as handle:
    # with open(f'/tmp/{token_id}.png', 'wb') as handle:
        response = requests.get(img_url, stream=True)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)
            
            
def save_image_send_tweet(nft_id, img_url, api, client, tweet):
    save_image_file(nft_id, img_url)                                
    # filename = f"/tmp/{token_id}.png"
    filename = f"{nft_id}.png"

    # upload saved image to twitter
    media = api.media_upload(filename)
    print("The media ID is : " + media.media_id_string)
    response = client.create_tweet(text=tweet, media_ids=[media.media_id_string])
    print(response)

    # remove saved image file
    os.remove(filename)
    
    
def get_img_url_gem_sweep(token_name, nft_id):
    if token_name == 'Azuki':
        url = f"https://ikzttp.mypinata.cloud/ipfs/QmYDvPAXtiJg7s8JdRBSLWdgSphQdac8j1YuQNNxcGE1hg/{nft_id}.png"
        return url
    else:
        url = f"https://ikzttp.mypinata.cloud/ipfs/QmTRuWHr7bpqscUWFmhXndzf5AdQqkekhqwgbyJCqKMHrL/{nft_id}.png"
        return url


def merge_dicts(dict1, dict2):
    """Given two dictionaries, merge them into a new dict as a shallow copy."""
    if type(dict1) is dict:
        if type(dict2) is dict:
            new_dict = dict1.copy()
            new_dict.update(dict2)
            return new_dict
        else:
            return dict1
    elif type(dict2) is dict:
        return dict2
    else:
        return 1
    

def lambda_handler(event, context):
    live_tweet=False # change to True to actually send out tweets. Otherwise it just prints Tweets to console.
    
    # Contracts:
    AZUKI = "0xed5af388653567af2f388e6224dc7c4b3241c544"
    BEANZ = "0x306b1ea3ecdf94aB739F1910bbda052Ed4A9f949"
    
    start_block = get_block_minutes_ago(5)
    end_block = 99999999
        
    # Test & Manual run block numbers:
    # start_block = 14718619
    # end_block = 14718619
    
    # 1.) get a list of all the transactions for a contract
    azuki_txns = get_transactions(AZUKI, start_block, end_block, True)
    beanz_txns = get_transactions(BEANZ, start_block, end_block, True)
    
    # 2.) Create txn dicts for each
    azuki_transactions = create_txn_dict(azuki_txns) if azuki_txns != 1 else 1
    beanz_transactions = create_txn_dict(beanz_txns) if beanz_txns != 1 else 1
    
    # 3.) Merge into 1 txn dict
    transactions = merge_dicts(azuki_transactions, beanz_transactions)
    print(transactions)

    # 4.) get most recent sale event from appropriate marketplace
    get_marketplace_event(transactions)    
    
    # 5.) create tweets for sales
    if live_tweet:
        client = twitter_auth_client_v2()
        api = twitter_auth_api_v1()
        
    for hash in transactions:
        marketplace = transactions[hash]['marketplace']
        num_sold = len(transactions[hash]['token_ids'])
        
        if num_sold == 1:
            if marketplace == 'OpenSea':
                for nft_id in transactions[hash]['token_ids']:
                    token_name = transactions[hash]['token_ids'][nft_id]['marketplace_event']['asset']['name']
                    sale_price = int(transactions[hash]['token_ids'][nft_id]['marketplace_event']['total_price']) / 10**18
                    usd_amount = sale_price * round(float((transactions[hash]['token_ids'][nft_id]['marketplace_event']['payment_token']['usd_price'])), 2)
                    marketplace_link = get_marketplace_link(marketplace, transactions[hash]['token_ids'][nft_id]['etherscan_data']['contractAddress'], nft_id)
                    
                    tweet = f"{token_name} sold for Ξ{sale_price} (${usd_amount:,.2f}) on {marketplace}.\n\n{EMOJIS['link']} {marketplace_link}\n{EMOJIS['receipt']} https://etherscan.io/tx/{hash}\n\n#Azuki #ikz"
                    print(tweet)
                    
                    img_url = transactions[hash]['token_ids'][nft_id]['marketplace_event']['asset']['image_original_url']
                    
                    if live_tweet:
                        save_image_send_tweet(nft_id, img_url, api, client, tweet)                                
            
            elif marketplace == 'LooksRare':
                for nft_id in transactions[hash]['token_ids']:
                    token_name = transactions[hash]['token_ids'][nft_id]['marketplace_event']['token']['name']
                    sale_price = int(transactions[hash]['token_ids'][nft_id]['marketplace_event']['order']['price']) / 10**18
                    usd_amount = sale_price * float(ethereum_price())
                    marketplace_link = get_marketplace_link(marketplace, transactions[hash]['token_ids'][nft_id]['etherscan_data']['contractAddress'], nft_id)
                    
                    tweet = f"{token_name} sold for Ξ{sale_price} (${usd_amount:,.2f}) on {marketplace}.\n\n{EMOJIS['link']} {marketplace_link}\n{EMOJIS['receipt']} https://etherscan.io/tx/{hash}\n\n#Azuki #ikz"
                    print(tweet)
                
                    img_url = transactions[hash]['token_ids'][nft_id]['marketplace_event']['token']['imageURI']
                    
                    if live_tweet:
                        save_image_send_tweet(nft_id, img_url, api, client, tweet)                                 
                            
            elif marketplace == 'Gem.xyz':
                # TODO if 1 token bought through Gem.xyz
                pass
            
        elif 2 <= num_sold <= 4:
            # Twitter only allows up to 4 images per Tweet, so save all images if number of NFTs sold is between 2 and 4
            if marketplace == "Gem.xyz":
                # Check if it's all the same NFT being sold
                nfts_sold = {}
                for nft_id in transactions[hash]['token_ids']:
                    token_name = transactions[hash]['token_ids'][nft_id]['etherscan_data']['tokenName']
                    
                    if token_name == 'Something':
                        token_name = 'Beanz'
                    
                    if token_name not in nfts_sold:
                        nfts_sold[token_name] = 1
                    else:
                        nfts_sold[token_name] += 1
                    
                print(nfts_sold)

                if len(nfts_sold) == 1:
                    # All the same type of NFT sold in this Gem Sweep. Proceed with a Tweet
                    sale_price = transactions[hash]['value'] / 10**18
                    usd_amount = sale_price * float(ethereum_price())
                    
                    tweet = f"{EMOJIS['broom']} {num_sold} {token_name} sold for Ξ{sale_price} (${usd_amount:,.2f}) on {marketplace} {EMOJIS['broom']}\nAverage price Ξ{sale_price / num_sold} (${usd_amount / num_sold:,.2f}).\n\n{EMOJIS['receipt']} https://etherscan.io/tx/{hash}\n\n#Azuki #ikz"
                    print(tweet)
                    
                    if live_tweet:
                        # Save the images for each NFT
                        media_ids = []
                        
                        for nft_id in transactions[hash]['token_ids']:           
                            # TODO - Get the URL for a gem sweep where it's not included
                            img_url = get_img_url_gem_sweep(token_name, nft_id)
                            
                            save_image_file(nft_id, img_url)                          
                            # filename = f"/tmp/{token_id}.png"
                            filename = f"{nft_id}.png"
                            
                            # upload to twitter and get media IDs
                            media = api.media_upload(filename)
                            print("The media ID is : " + media.media_id_string)
                            media_ids.append(media.media_id_string)
                            
                            # remove local file
                            os.remove(filename)
                        
                        # Send tweet
                        response = client.create_tweet(text=tweet, media_ids=media_ids)
                        print(response)

                else:
                    # TODO - If multiple types of NFTs sold in this gem sweep
                    pass
                
        else:
            # If number of NFTs sold in 1 transaction is > 4
            if marketplace == "Gem.xyz":
                # check if it's all the same NFT being sold
                nfts_sold = {}
                for nft_id in transactions[hash]['token_ids']:
                    token_name = transactions[hash]['token_ids'][nft_id]['etherscan_data']['tokenName']
                    
                    if token_name == 'Something':
                        token_name = 'Beanz'
                        
                    if token_name not in nfts_sold:
                        nfts_sold[token_name] = 1
                    else:
                        nfts_sold[token_name] += 1
                    
                if len(nfts_sold) == 1:
                    # All the same type of NFT sold in this Gem Sweep. Proceed with a Tweet
                    sale_price = transactions[hash]['value'] / 10**18
                    usd_amount = sale_price * float(ethereum_price())
                    
                    tweet = f"{EMOJIS['broom']} {num_sold} {token_name} sold for Ξ{sale_price} (${usd_amount:,.2f}) on {marketplace} {EMOJIS['broom']}\nAverage price Ξ{sale_price / num_sold} (${usd_amount / num_sold:,.2f}).\n\n{EMOJIS['receipt']} https://etherscan.io/tx/{hash}\n\n#Azuki #ikz"
                    print(tweet)
                    
                    if live_tweet:
                        response = client.create_tweet(text=tweet)
                        print(response)

                else:
                    # multiple types of NFTs sold in this gem sweep. Work on this later.
                    pass