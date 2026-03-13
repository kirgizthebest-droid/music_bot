from telegram import LabeledPrice

PACKAGES = {

    "pack_3": {
        "title": "3 песни",
        "credits": 3,
        "price_stars": 100,
        "price_rub": 199,
        "price_usdt": 2
    },

    "pack_10": {
        "title": "10 песен",
        "credits": 10,
        "price_stars": 250,
        "price_rub": 399,
        "price_usdt": 4
    },

    "pack_50": {
        "title": "50 песен",
        "credits": 50,
        "price_stars": 900,
        "price_rub": 999,
        "price_usdt": 10
    }

}


def create_invoice(package):

    pack = PACKAGES[package]

    prices = [LabeledPrice(pack["title"], pack["price_stars"])]

    return prices
