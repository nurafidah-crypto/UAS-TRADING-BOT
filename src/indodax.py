
import requests

BASE_URL = "https://indodax.com"


# =====================================
# 1. MENGAMBIL DATA TICKER
# =====================================

def get_ticker():
    url = f"{BASE_URL}/api/ticker_all"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()
        return data.get("tickers", {})

    except Exception as e:
        print("Gagal mengambil ticker:", e)
        return {}


# =====================================
# 2. MENGAMBIL DATA ORDER BOOK
# =====================================

def get_order_book(pair="btcidr"):
    url = f"{BASE_URL}/api/depth/{pair}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        return {
            "bids": data.get("buy", []),
            "asks": data.get("sell", [])
        }

    except Exception as e:
        print("Gagal mengambil order book:", e)
        return None


# =====================================
# 3. MENJALANKAN PENGUJIAN
# =====================================

if __name__ == "__main__":

    print("MENGHUBUNGKAN KE INDODAX...")
    print("==========================")

    # Mengambil ticker
    tickers = get_ticker()

    if tickers:
        print("\nKONEKSI INDODAX BERHASIL!")
        print("Daftar pasangan tersedia:")
        print(list(tickers.keys())[:20])

        btc = tickers.get("btcidr") or tickers.get("btc_idr")

        if btc:
            print("\nHARGA BITCOIN")
            print("Last price:", btc["last"])
            print("Buy:", btc["buy"])
            print("Sell:", btc["sell"])
    else:
        print("\nGagal mengambil data ticker.")

    # Mengambil order book
    print("\nORDER BOOK BTC/IDR")
    order_book = get_order_book()

    if order_book:
        bids = order_book["bids"]
        asks = order_book["asks"]

        if bids and asks:
            print("Bid terbaik:", bids[0])
            print("Ask terbaik:", asks[0])

            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])

            spread = best_ask - best_bid
            spread_percent = spread / best_ask * 100

            print("\nSPREAD BTC/IDR")
            print("Selisih harga:", spread)
            print("Spread (%):", round(spread_percent, 4), "%")
        else:
            print("Order book kosong.")
    else:
        print("Gagal mengambil order book.")
