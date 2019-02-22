import json

from .models import Item


class ItemHelper:
    def __init__(self):
        with open('./vainlab/_item.json', 'r') as f:
            self.item_tier = json.load(f)
        with open('./vainlab/_item_t3.json', 'r') as f:
            self.item_t3id = json.load(f)
