import requests
import json
import pandas as pd
from pandas import json_normalize

def get_price_lookup():
    url = "https://weav3r.dev/api/pricelist/4253363"
    price_response = requests.get(url)
    price_data = price_response.json()
    price_lookup = {}

    for item in price_data:
        item_id = item["itemId"]
        price = item["buyPrice"]

        price_lookup[item_id] = price

    return price_lookup

def inventory(api_key):
    categorie = [
    "Flower",
    "Plushie",
    ]

    price_lookup = get_price_lookup()

    inventory_tables = {}

    def get_inventory_data(categorie):
        url = f"https://api.torn.com/v2/user/inventory?cat={categorie}&offset=0&limit=20&key={api_key}"
        response = requests.get(url)
        return response    
    # Iterate through all categories and fetch inventory data for each
    for categorie in categorie:
        response = get_inventory_data(categorie)

        data = response.json()
        if "inventory" not in data:
            print(data)
            return {}
        #normalize the inventory data for the current category
        categorie_json_inventory = json_normalize(data['inventory'])
        
        categorie_json_items = json_normalize(categorie_json_inventory['items'].explode())

        #map the price lookup to the items and calculate total value
        categorie_json_items["price"] = categorie_json_items["id"].map(price_lookup)
        categorie_json_items["amount"] = pd.to_numeric(categorie_json_items["amount"], errors='coerce').fillna(0)
        categorie_json_items["price"] = pd.to_numeric(categorie_json_items["price"], errors='coerce').fillna(0)
        categorie_json_items["total_value"] = categorie_json_items["amount"] * categorie_json_items["price"]

        categorie_json_items = categorie_json_items.drop(columns=['id', 'equipped', 'uid', 'faction_owned'], errors='ignore')
        
        inventory_tables[categorie] = categorie_json_items

    return inventory_tables