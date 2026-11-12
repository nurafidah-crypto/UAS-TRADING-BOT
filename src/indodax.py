
import time
import requests

BASE_URL = "https://indodax.com"
REQUEST_TIMEOUT = 15


# =====================================
# 1. MENGAMBIL DATA TICKER
# =====================================

def get_ticker():
    url = f"{BASE_URL}/api/ticker_all"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        return data.get("tickers", {})

    except (
        requests.RequestException,
        ValueError,
        TypeError
    ) as error:
        print("Gagal mengambil ticker:", error)
        return {}


# =====================================
# 2. MENGAMBIL DATA ORDER BOOK
# =====================================

def get_order_book(pair="btcidr"):
    pair = str(pair).lower().strip()

    if not pair:
        raise ValueError("Pair tidak boleh kosong.")

    url = f"{BASE_URL}/api/depth/{pair}"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return None

        bids = data.get("buy", [])
        asks = data.get("sell", [])

        if not isinstance(bids, list):
            return None

        if not isinstance(asks, list):
            return None

        return {
            "bids": bids,
            "asks": asks,
            "fetched_at": time.time()
        }

    except (
        requests.RequestException,
        ValueError,
        TypeError
    ) as error:
        print(
            f"Gagal mengambil order book {pair}:",
            error
        )
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

        btc = (
            tickers.get("btcidr")
            or tickers.get("btc_idr")
        )

        if btc:
            print("\nHARGA BITCOIN")
            print("Last price:", btc.get("last"))
            print("Buy:", btc.get("buy"))
            print("Sell:", btc.get("sell"))

    else:
        print("\nGagal mengambil data ticker.")

    # Mengambil order book
    print("\nORDER BOOK BTC/IDR")

    order_book = get_order_book("btcidr")

    if order_book:

        bids = order_book["bids"]
        asks = order_book["asks"]

        if bids and asks:

            print("Bid terbaik:", bids[0])
            print("Ask terbaik:", asks[0])

            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])

            if best_bid > 0 and best_ask > 0:

                spread = best_ask - best_bid
                spread_percent = (
                    spread / best_ask * 100
                )

                print("\nSPREAD BTC/IDR")
                print("Selisih harga:", spread)
                print(
                    "Spread (%):",
                    round(spread_percent, 4),
                    "%"
                )

            else:
                print("Harga bid atau ask tidak valid.")

            print(
                "Waktu pengambilan:",
                order_book["fetched_at"]
            )

        else:
            print("Order book kosong.")

    else:
        print("Gagal mengambil data order book.")
