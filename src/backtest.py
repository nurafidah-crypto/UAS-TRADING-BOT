import pandas as pd

FILE = "data/btcidr_indicators.csv"

INITIAL_CAPITAL = 100_000_000
FEE_RATE = 0.003  # Asumsi sementara 0,3% per sisi

df = pd.read_csv(FILE)

cash = INITIAL_CAPITAL
btc = 0
entry_cost = 0
entry_price = 0
entry_time = None

trades = []
equity_curve = []

for i in range(1, len(df)):
    previous = df.iloc[i - 1]
    current = df.iloc[i]

    price = current["Open"]

    if pd.isna(price) or price <= 0:
        continue

    buy_signal = previous["Buy_Signal"] == True

    sell_signal = (
        previous["EMA_20"] <= previous["EMA_50"]
        or previous["RSI_14"] < 45
    )

    # Beli berdasarkan sinyal candle sebelumnya
    if btc == 0 and buy_signal:
        investment = cash * 0.95
        fee = investment * FEE_RATE

        btc = (investment - fee) / price
        cash -= investment

        entry_cost = investment
        entry_price = price
        entry_time = current["Time"]

    # Jual berdasarkan sinyal candle sebelumnya
    elif btc > 0 and sell_signal:
        quantity = btc
        gross_revenue = quantity * price
        fee = gross_revenue * FEE_RATE
        net_revenue = gross_revenue - fee

        pnl = net_revenue - entry_cost

        trades.append({
            "Entry_Time": entry_time,
            "Exit_Time": current["Time"],
            "Entry_Price": entry_price,
            "Exit_Price": price,
            "Quantity": quantity,
            "Entry_Cost": entry_cost,
            "Exit_Revenue": net_revenue,
            "Profit_Loss": pnl,
            "Return_Percent": pnl / entry_cost * 100
        })

        cash += net_revenue
        btc = 0
        entry_cost = 0

    equity = cash + btc * current["Close"]

    equity_curve.append({
        "Time": current["Time"],
        "Equity": equity
    })

# Nilai akhir portofolio
final_equity = cash + btc * df.iloc[-1]["Close"]

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

print("HASIL BACKTEST REVISI")
print("=====================")
print("Modal awal: Rp", round(INITIAL_CAPITAL))
print("Modal akhir: Rp", round(final_equity))
print("Total return:", round(total_return, 2), "%")
print("Jumlah siklus selesai:", len(trades_df))
print("Win rate:", round(win_rate, 2), "%")
print("Profit factor:", round(profit_factor, 2))

print("\nJumlah transaksi untung:",
      len(trades_df[trades_df["Profit_Loss"] > 0]))

print("Jumlah transaksi rugi:",
      len(trades_df[trades_df["Profit_Loss"] < 0]))

print("Posisi BTC tersisa:", btc)

trades_df.to_csv("data/backtest_trades_revised.csv", index=False)
equity_df.to_csv("data/equity_curve_revised.csv", index=False)

print("\nFile transaksi: data/backtest_trades_revised.csv")
print("File equity: data/equity_curve_revised.csv")