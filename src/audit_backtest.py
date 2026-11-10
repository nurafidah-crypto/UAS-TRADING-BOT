import pandas as pd

df = pd.read_csv("data/backtest_trades.csv")

df["Time"] = pd.to_numeric(df["Time"])
df["Tanggal"] = pd.to_datetime(df["Time"], unit="s", utc=True)

buys = df[df["Type"] == "BUY"].reset_index(drop=True)
sells = df[df["Type"] == "SELL"].reset_index(drop=True)

print("AUDIT HASIL BACKTEST")
print("====================")
print("Jumlah BUY:", len(buys))
print("Jumlah SELL:", len(sells))

if len(buys) == len(sells):
    holding_hours = (
        sells["Time"].values - buys["Time"].values
    ) / 3600

    print("\nRATA-RATA LAMA HOLDING:")
    print(round(holding_hours.mean(), 2), "jam")

    print("\nTRANSAKSI PERTAMA:")
    print("BUY :", buys.iloc[0]["Tanggal"])
    print("SELL:", sells.iloc[0]["Tanggal"])

    print("\n10 TRANSAKSI TERAKHIR:")
    print(df.tail(10).to_string(index=False))
else:
    print("Jumlah BUY dan SELL tidak sama.")