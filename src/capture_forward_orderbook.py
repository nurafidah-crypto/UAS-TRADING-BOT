
import csv
import os
from datetime import datetime, timezone

from indodax import get_order_book

OUTPUT_FILE = "data/forward_test/orderbook/snapshots.csv"

PAIRS = [
    "btcidr",
    "ethidr",
    "xrpidr",
    "solidr",
    "pepeidr",
    "hypeidr",
]


def capture_forward_orderbook():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    file_exists = (
        os.path.exists(OUTPUT_FILE)
        and os.path.getsize(OUTPUT_FILE) > 0
    )

    total_saved = 0

    with open(
        OUTPUT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Pair",
                "Side",
                "Price",
                "Amount"
            ])

        for pair in PAIRS:
            timestamp = datetime.now(timezone.utc).isoformat()

            try:
                order_book = get_order_book(pair)

                if not order_book:
                    print(f"Gagal mengambil order book: {pair}")
                    continue

                bids = order_book.get("bids", [])
                asks = order_book.get("asks", [])

                if not bids or not asks:
                    print(f"Order book kosong: {pair}")
                    continue

                saved = 0

                for price, amount in bids[:20]:
                    writer.writerow([
                        timestamp, pair, "BID", price, amount
                    ])
                    saved += 1

                for price, amount in asks[:20]:
                    writer.writerow([
                        timestamp, pair, "ASK", price, amount
                    ])
                    saved += 1

                total_saved += saved

                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])

                midpoint = (best_bid + best_ask) / 2
                spread_percent = (
                    (best_ask - best_bid) / midpoint * 100
                )

                print(
                    f"{pair.upper()}: "
                    f"bid={best_bid}, ask={best_ask}, "
                    f"spread={spread_percent:.6f}%, "
                    f"level={saved}"
                )

            except Exception as error:
                print(f"Error pada {pair}: {error}")

        file.flush()

    print("\nFORWARD ORDER BOOK SNAPSHOT SELESAI")
    print("Total baris tersimpan:", total_saved)
    print("File:", OUTPUT_FILE)


if __name__ == "__main__":
    capture_forward_orderbook()
