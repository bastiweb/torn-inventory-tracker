import requests
import pandas as pd
from pandas import json_normalize

def get_price_lookup(trader_id):
    url = f"https://weav3r.dev/api/pricelist/{trader_id}"
    price_response = requests.get(url, timeout=15)
    price_data = price_response.json()
    price_lookup = {}

    if not isinstance(price_data, list):
        raise ValueError(f"Invalid price list response: {price_data}")
    
    for item in price_data:
        item_id = item["itemId"]
        price = item["buyPrice"]

        price_lookup[item_id] = price

    return price_lookup

def inventory(api_key, trader_id, categories=["Flower", "Plushie"]):
    
    price_lookup = get_price_lookup(trader_id)

    inventory_tables = {}

    def get_inventory_data(category):
        url = f"https://api.torn.com/v2/user/inventory?cat={category}&offset=0&limit=20&key={api_key}"
        response = requests.get(url, timeout=15)
        return response    
    # Iterate through all categories and fetch inventory data for each
    for category in categories:
        response = get_inventory_data(category)

        data = response.json()
        if "inventory" not in data:
            print(data)
            return {}
        #normalize the inventory data for the current category
        category_json_inventory = json_normalize(data['inventory'])
        
        category_json_items = json_normalize(category_json_inventory['items'].explode())

        #map the price lookup to the items and calculate total value
        category_json_items["price"] = category_json_items["id"].map(price_lookup)
        category_json_items["amount"] = pd.to_numeric(category_json_items["amount"], errors='coerce').fillna(0)
        category_json_items["price"] = pd.to_numeric(category_json_items["price"], errors='coerce').fillna(0)
        category_json_items["total_value"] = category_json_items["amount"] * category_json_items["price"]

        category_json_items = category_json_items.drop(columns=['id', 'equipped', 'uid', 'faction_owned'], errors='ignore')
        
        inventory_tables[category] = category_json_items

    return inventory_tables