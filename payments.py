from telegram import LabeledPrice

PACKAGES = {

    "pack_3": {
        "title": "3 песни",
        "credits": 3,
        "price": 100
    },

    "pack_10": {
        "title": "10 песен",
        "credits": 10,
        "price": 250
    },

    "pack_50": {
        "title": "50 песен",
        "credits": 50,
        "price": 900
    }

}


def create_invoice(package):

    pack = PACKAGES[package]

    prices = [LabeledPrice(pack["title"], pack["price"])]

    return prices
