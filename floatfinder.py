import time
import random
import requests
import json
import os

# ---- Config ----
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

SKIN_NAME = "AK-47 | Redline (Field Tested)"   # change this to any market skin name
FLOAT_MIN = 0.0000   # desired float range min
FLOAT_MAX = 0.1   # desired float range max
SCAN_INTERVAL = 10   # seconds between scans

# Gentle request to Steam API with retries
def gentle_request(url, method="get", max_retries=5, backoff=2, **kwargs):
    for attempt in range(max_retries):
        try:
            if method == "get":
                r = requests.get(url, timeout=10, **kwargs)
            else:
                r = requests.post(url, timeout=10, **kwargs)

            if r.status_code == 200:
                return r
            else:
                print(f"Request failed (status {r.status_code}), attempt {attempt+1}/{max_retries}")
        except requests.exceptions.RequestException as e:
            print(f"Socket error: {e}, attempt {attempt+1}/{max_retries}")

        sleep_time = backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
        print(f"Sleeping {sleep_time:.2f}s before retry...")
        time.sleep(sleep_time)

    return None

# Telegram
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Telegram send failed: {e}")

# Steam Market API call
def get_market_data(skin_name):
    skin_url_name = skin_name.replace(" ", "%20").replace("|", "%7C").replace("(", "%28").replace(")", "%29")
    skin_url = f"https://steamcommunity.com/market/listings/730/{skin_url_name}/render?currency=1&start={{start}}"

    listings = []
    for start in (0, 10):
        r = gentle_request(skin_url.format(start=start), "get")
        if not r:
            continue

        text = r.text
        try:
            json_part = text[text.find("{"):]  # cut off response HTML
            data = json.loads(json_part)
        except Exception:
            print("Failed to parse JSON, if this says 'null' then the request was bad:", text[:200])
            continue

        listinginfo = data.get("listinginfo", {})
        assets = data.get("assets", {}).get("730", {}).get("2", {})

        for listing_id, listing in listinginfo.items():
            try:
                price_val = (listing["converted_price"] + listing["converted_fee"]) / 100
            except:
                price_val = 0.0

            assetid = listing.get("asset", {}).get("id")
            asset = assets.get(assetid, {})
            inspect_link = None

            if "market_actions" in asset and asset["market_actions"]:
                template = asset["market_actions"][0]["link"]
                inspect_link = (
                    template.replace("%listingid%", listing_id)
                           .replace("%assetid%", assetid)
                )

            if inspect_link:
                listings.append({
                    "inspect_link": inspect_link,
                    "price": price_val,
                    "listing_id": listing_id
                })

    if listings:
        print(f"[DEBUG] First inspect link: {listings[0]['inspect_link']}")
    else:
        print("[DEBUG] No listings parsed")

    return listings

# Check floats using CSfloat API hosted locally, listening on port 80
def fetch_float(inspect_link):
    """Query local CSFloat API with inspect link"""
    url = "http://localhost:80/"
    try:
        r = requests.get(url, params={"url": inspect_link}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("iteminfo", {}).get("floatvalue")
        else:
            print(f"Float API bad response {r.status_code}")
    except Exception as e:
        print(f"Float fetch error: {e}")
    return None

# Grab skins, fetch floats
def check_skin(skin_name, float_min, float_max):
    print(f"Checking {skin_name}...")
    listings = get_market_data(skin_name)
    if not listings:
        print("No listings found")
        return

    # find cheapest price among fetched listings
    cheapest_price = min(l["price"] for l in listings if l["price"] > 0)
    price_threshold = cheapest_price * 1.15
    print(f"Cheapest price: ${cheapest_price:.2f}, threshold: ${price_threshold:.2f}")

    for i, listing in enumerate(listings):
        fval = fetch_float(listing["inspect_link"])
        listing["float"] = fval

        print(f"Listing {i+1}: Price ${listing['price']:.2f}, Float {fval}")

        time.sleep(0.3)

        if fval is not None and float_min <= fval <= float_max:
            if listing["price"] <= price_threshold:
                buy_link = f"https://steamcommunity.com/market/listings/730/{skin_name.replace(' ', '%20').replace('|', '%7C').replace('(', '%28').replace(')', '%29')}#buylistingid={listing['listing_id']}"
                msg = (
                    f"Desired float found!\n"
                    f"Skin: {skin_name}\n"
                    f"Float: {fval:.6f}\n"
                    f"Price: ${listing['price']:.2f} (≤ {price_threshold:.2f})\n"
                    f"Inspect: {listing['inspect_link']}\n"
                    f"Buy Now: {buy_link}"
                )
                send_telegram(msg)
                print("[ALERT]", msg)
            else:
                print(f"Float matched but too expensive: ${listing['price']:.2f} > ${price_threshold:.2f}")

# main loop
if __name__ == "__main__":
    send_telegram(f"Bot started. Watching: {SKIN_NAME} (Float {FLOAT_MIN}–{FLOAT_MAX}, ≤115% cheapest)")

    while True:
        check_skin(SKIN_NAME, FLOAT_MIN, FLOAT_MAX)
        time.sleep(SCAN_INTERVAL)
