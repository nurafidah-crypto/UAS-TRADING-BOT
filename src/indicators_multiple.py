
import os
import glob
import pandas as pd

INPUT_DIR = "data/historical_3y"
OUTPUT_DIR = "data/indicators"

os.makedirs(OUTPUT_DIR, exist_ok=True)

files = glob.glob(
    os.path.join(INPUT_DIR, "*_3tahun.csv")
)

print("MEMBUAT INDIKATOR MULTI-PAIR")
print("============================")

for file_path in sorted(files):

    filename = os.path.basename(file_path)
    pair = filename.replace("_3tahun.csv", "").upper()

    print("\nMemproses:", pair)

    df = pd.read_csv(file_path)

    # Pastikan data tersusun berdasarkan waktu.
    df = df.sort_values("Time").reset_index(drop=True)

    # Tandai candle yang memiliki aktivitas trading.
    df["Valid_Trading"] = df["Volume"] > 0

    # EMA 20 dan EMA 50.
    df["EMA_20"] = df["Close"].ewm(
        span=20,
        adjust=False
    ).mean()

    df["EMA_50"] = df["Close"].ewm(
        span=50,
        adjust=False
    ).mean()

    # RSI 14.
    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        adjust=False,
        min_periods=14
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        adjust=False,
        min_periods=14
    ).mean()

    rs = avg_gain / avg_loss

    df["RSI_14"] = 100 - (100 / (1 + rs))

    # Tangani kondisi harga selalu naik atau tidak bergerak.
    df.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "RSI_14"
    ] = 100

    df.loc[
        (avg_loss == 0) & (avg_gain == 0),
        "RSI_14"
    ] = 50

    # Sinyal beli.
    df["Buy_Signal"] = (
        (df["EMA_20"] > df["EMA_50"]) &
        (df["RSI_14"] > 50) &
        (df["RSI_14"] < 70) &
        (df["Valid_Trading"])
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        pair.lower() + "_indicators.csv"
    )

    df.to_csv(output_file, index=False)

    print("Jumlah candle:", len(df))
    print("Volume nol:", (~df["Valid_Trading"]).sum())
    print("Jumlah sinyal beli:", int(df["Buy_Signal"].sum()))
    print("File:", output_file)

print("\n============================")
print("SEMUA INDIKATOR SELESAI")
