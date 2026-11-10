
import pandas as pd
import glob
import os

# =====================================
# PENGATURAN BACKTEST
# =====================================

INITIAL_CAPITAL = 100_000_000
FEE_RATE = 0.003  # Asumsi sementara 0,3% per sisi
MAX_POSITIONS = 3
MAX_ALLOCATION = 0.30  # Maksimal 30% modal untuk setiap pair

INPUT_FILES = glob.glob("data/indicators/*_indicators.csv")

# =====================================
# MEMUAT DATA SEMUA PAIR
# =====================================

market_data = {}

for file in INPUT_FILES:
    pair = os.path.basename(file).replace("_indicators.csv", "").upper()

    df = pd.read_csv(file)
    df = df.sort_values("Time").reset_index(drop=True)

    market_data[pair] = df

    print(pair, "-", len(df), "candles")

# =====================================
# MENYATUKAN WAKTU SEMUA PAIR
# =====================================

all_times = sorted(set(
    time
    for df in market_data.values()
    for time in df["Time"]
))

data_by_pair = {}

for pair, df in market_data.items():
    data_by_pair[pair] = df.set_index("Time")

# =====================================
# PORTOFOLIO
# =====================================

cash = INITIAL_CAPITAL
positions = {}
trades = []
equity_curve = []

for time in all_times:

    # ---------------------------------
    # PROSES JUAL
    # ---------------------------------

    for pair in list(positions.keys()):

        df = data_by_pair[pair]

        if time not in df.index:
            continue

        current = df.loc[time]

        if isinstance(current, pd.DataFrame):
            current = current.iloc[-1]

        previous_rows = df.loc[df.index < time]

        if previous_rows.empty:
            continue

        previous = previous_rows.iloc[-1]

        sell_signal = (
            previous["EMA_20"] <= previous["EMA_50"]
            or previous["RSI_14"] < 45
        )

        if sell_signal and current["Open"] > 0:

            position = positions[pair]

            quantity = position["quantity"]
            gross = quantity * current["Open"]
            fee = gross * FEE_RATE
            net = gross - fee

            pnl = net - position["entry_cost"]

            trades.append({
                "Pair": pair,
                "Entry_Time": position["entry_time"],
                "Exit_Time": time,
                "Entry_Cost": position["entry_cost"],
                "Exit_Revenue": net,
                "Profit_Loss": pnl,
                "Return_Percent": pnl / position["entry_cost"] * 100
            })

            cash += net
            del positions[pair]

    # ---------------------------------
    # PROSES BELI
    # ---------------------------------

    for pair in market_data.keys():

        if pair in positions:
            continue

        if len(positions) >= MAX_POSITIONS:
            break

        df = data_by_pair[pair]

        if time not in df.index:
            continue

        current = df.loc[time]

        if isinstance(current, pd.DataFrame):
            current = current.iloc[-1]

        previous_rows = df.loc[df.index < time]

        if previous_rows.empty:
            continue

        previous = previous_rows.iloc[-1]

        buy_signal = (
            previous["Buy_Signal"] == True
        )

        if (
            buy_signal
            and current["Open"] > 0
            and current["Valid_Trading"] == True
        ):

            investment = min(
                cash * MAX_ALLOCATION,
                INITIAL_CAPITAL * MAX_ALLOCATION
            )

            if investment <= 0:
                continue

            fee = investment * FEE_RATE
            quantity = (investment - fee) / current["Open"]

            cash -= investment

            positions[pair] = {
                "quantity": quantity,
                "entry_cost": investment,
                "entry_time": time,
                "entry_price": current["Open"]
            }

    # ---------------------------------
    # HITUNG EQUITY
    # ---------------------------------

    equity = cash

    for pair, position in positions.items():

        df = data_by_pair[pair]
        available = df.loc[df.index <= time]

        if available.empty:
            continue

        latest = available.iloc[-1]

        equity += (
            position["quantity"] * latest["Close"]
        )

    equity_curve.append({
        "Time": time,
        "Equity": equity,
        "Cash": cash,
        "Open_Positions": len(positions)
    })

# =====================================
# HASIL AKHIR
# =====================================

final_equity = equity_curve[-1]["Equity"]

total_return = (
    final_equity / INITIAL_CAPITAL - 1
) * 100

trades_df = pd.DataFrame(trades)
equity_df = pd.DataFrame(equity_curve)

if len(trades_df) > 0:

    wins = trades_df[trades_df["Profit_Loss"] > 0]
    losses = trades_df[trades_df["Profit_Loss"] < 0]

    win_rate = len(wins) / len(trades_df) * 100

    gross_profit = wins["Profit_Loss"].sum()
    gross_loss = abs(losses["Profit_Loss"].sum())

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0 else float("inf")
    )

else:
    win_rate = 0
    profit_factor = 0

# =====================================
# SIMPAN HASIL
# =====================================

trades_df.to_csv(
    "data/backtest_multi_trades.csv",
    index=False
)

equity_df.to_csv(
    "data/backtest_multi_equity.csv",
    index=False
)

print("\nHASIL BACKTEST MULTI-PAIR")
print("=========================")
print("Modal awal: Rp", round(INITIAL_CAPITAL))
print("Modal akhir: Rp", round(final_equity))
print("Total return:", round(total_return, 2), "%")
print("Jumlah transaksi selesai:", len(trades_df))
print("Win rate:", round(win_rate, 2), "%")
print("Profit factor:", round(profit_factor, 2))
print("Posisi tersisa:", len(positions))
print("Cash tersisa: Rp", round(cash))

print("\nFile transaksi: data/backtest_multi_trades.csv")
print("File equity: data/backtest_multi_equity.csv")
