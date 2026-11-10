
import os
import glob
import pandas as pd

FOLDER = "data/historical_3y"
FILES = glob.glob(os.path.join(FOLDER, "*_3tahun.csv"))

print("VALIDASI DATA HISTORIS SEMUA PAIR")
print("=================================")

summary = []

for file_path in sorted(FILES):

    pair = os.path.basename(file_path).replace(
        "_3tahun.csv", ""
    ).upper()

    df = pd.read_csv(file_path)

    required = ["Time", "Open", "High", "Low", "Close", "Volume"]

    missing_columns = [
        col for col in required if col not in df.columns
    ]

    if missing_columns:
        print(f"\n{pair}: KOLOM TIDAK LENGKAP:", missing_columns)
        continue

    df["Time"] = pd.to_numeric(df["Time"], errors="coerce")

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    invalid_rows = df[required].isna().any(axis=1).sum()
    duplicate_count = df["Time"].duplicated().sum()

    valid_time = df.dropna(subset=["Time"]).sort_values("Time")

    time_diffs = valid_time["Time"].diff().dropna()
    gap_count = (time_diffs > 3600).sum()
    irregular_count = (time_diffs != 3600).sum()

    invalid_ohlc = (
        (df["High"] < df["Low"]) |
        (df["High"] < df["Open"]) |
        (df["High"] < df["Close"]) |
        (df["Low"] > df["Open"]) |
        (df["Low"] > df["Close"]) |
        (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1) |
        (df["Volume"] < 0)
    ).sum()

    zero_volume = (df["Volume"] == 0).sum()

    first_time = valid_time["Time"].min()
    last_time = valid_time["Time"].max()

    first_date = pd.to_datetime(
        first_time, unit="s", utc=True
    )
    last_date = pd.to_datetime(
        last_time, unit="s", utc=True
    )

    summary.append({
        "Pair": pair,
        "Candles": len(df),
        "Duplicates": duplicate_count,
        "Missing_Values": invalid_rows,
        "Gap_Count": gap_count,
        "Irregular_Intervals": irregular_count,
        "Invalid_OHLC": invalid_ohlc,
        "Zero_Volume": zero_volume,
        "First_Candle_UTC": first_date,
        "Last_Candle_UTC": last_date
    })

    print(f"\nPAIR: {pair}")
    print("Jumlah candle:", len(df))
    print("Duplikasi:", duplicate_count)
    print("Baris dengan nilai kosong:", invalid_rows)
    print("Gap lebih dari 1 jam:", gap_count)
    print("Interval tidak tepat 1 jam:", irregular_count)
    print("OHLC tidak valid:", invalid_ohlc)
    print("Volume nol:", zero_volume)
    print("Data pertama:", first_date)
    print("Data terakhir:", last_date)

if summary:
    result = pd.DataFrame(summary)
    result.to_csv(
        "data/validation_summary.csv",
        index=False
    )

    print("\n=================================")
    print("VALIDASI SELESAI")
    print("File: data/validation_summary.csv")
