
import os
import glob
import pandas as pd
import numpy as np

# ============================================================
# KONFIGURASI BACKTEST
# ============================================================

INITIAL_CAPITAL = 100_000_000
FEE_RATE = 0.003              # Asumsi fee 0,3% per sisi
FULL_SPREAD_RATE = 0.0004     # Asumsi spread penuh 0,04%
SLIPPAGE_RATE = 0.0005        # Asumsi slippage 0,05% per sisi

MAX_POSITIONS = 3
MAX_ALLOCATION = 0.30         # Maksimal 30% modal awal per posisi

INDICATOR_FOLDER = "data/indicators"
OUTPUT_FOLDER = "data/backtest"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

BUY_COST_RATE = (FULL_SPREAD_RATE / 2) + SLIPPAGE_RATE
SELL_COST_RATE = (FULL_SPREAD_RATE / 2) + SLIPPAGE_RATE


# ============================================================
# FUNGSI BANTU
# ============================================================

def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def load_data():
    files = sorted(glob.glob(
        os.path.join(INDICATOR_FOLDER, "*_indicators.csv")
    ))

    if not files:
        raise FileNotFoundError(
            "Tidak ada file indikator di data/indicators/"
        )

    data = {}

    for file in files:
        pair = os.path.basename(file).replace(
            "_indicators.csv", ""
        ).upper()

        df = pd.read_csv(file)

        required = [
            "Time", "Open", "Close", "Valid_Trading",
            "EMA_20", "EMA_50", "RSI_14", "Buy_Signal"
        ]

        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(
                f"Kolom {missing} tidak ditemukan di {file}"
            )

        df["Time"] = pd.to_datetime(df["Time"], unit="s", utc=True)
        numeric_cols = [
            "Open", "Close", "EMA_20", "EMA_50", "RSI_14"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["Valid_Trading"] = df["Valid_Trading"].apply(to_bool)
        df["Buy_Signal"] = df["Buy_Signal"].apply(to_bool)

        df = (
            df.dropna(subset=["Time", "Open", "Close"])
              .sort_values("Time")
              .drop_duplicates(subset=["Time"], keep="last")
              .set_index("Time")
        )

        data[pair] = df

    return data


def execution_buy(open_price):
    return open_price * (1 + BUY_COST_RATE)


def execution_sell(open_price):
    return open_price * (1 - SELL_COST_RATE)


# ============================================================
# BACKTEST
# ============================================================

def run_backtest():
    data = load_data()

    all_times = sorted(set().union(
        *[set(df.index) for df in data.values()]
    ))

    cash = INITIAL_CAPITAL
    positions = {}
    trades = []
    equity_history = []

    previous_rows = {pair: None for pair in data}

    for timestamp in all_times:

        current_rows = {}

        for pair, df in data.items():
            if timestamp in df.index:
                current_rows[pair] = df.loc[timestamp]

        # ----------------------------------------------------
        # 1. JUAL POSISI BERDASARKAN SINYAL CANDLE SEBELUMNYA
        # ----------------------------------------------------

        for pair in sorted(list(positions.keys())):
            previous = previous_rows.get(pair)

            if previous is None:
                continue

            should_sell = (
                previous["EMA_20"] <= previous["EMA_50"]
                or previous["RSI_14"] < 45
            )

            row = current_rows.get(pair)

            if should_sell and row is not None:
                open_price = row["Open"]

                if not np.isfinite(open_price) or open_price <= 0:
                    continue

                position = positions[pair]
                sell_price = execution_sell(open_price)

                gross_sell = position["quantity"] * sell_price
                sell_fee = gross_sell * FEE_RATE
                net_proceeds = gross_sell - sell_fee

                cash += net_proceeds

                net_pnl = net_proceeds - position["total_buy_cost"]

                trades.append({
                    "Pair": pair,
                    "Entry_Time": position["entry_time"],
                    "Exit_Time": timestamp,
                    "Entry_Price": position["buy_price"],
                    "Exit_Price": sell_price,
                    "Quantity": position["quantity"],
                    "Buy_Fee": position["buy_fee"],
                    "Sell_Fee": sell_fee,
                    "Total_Fees": position["buy_fee"] + sell_fee,
                    "Net_PnL": net_pnl,
                    "Return_Percent": (
                        net_pnl / position["total_buy_cost"] * 100
                    ),
                    "Exit_Type": "Signal"
                })

                del positions[pair]

        # ----------------------------------------------------
        # 2. BELI BERDASARKAN SINYAL CANDLE SEBELUMNYA
        # ----------------------------------------------------

        for pair in sorted(data.keys()):

            if pair in positions:
                continue

            if len(positions) >= MAX_POSITIONS:
                break

            previous = previous_rows.get(pair)
            row = current_rows.get(pair)

            if previous is None or row is None:
                continue

            if not previous["Buy_Signal"]:
                continue

            if not row["Valid_Trading"]:
                continue

            open_price = row["Open"]

            if not np.isfinite(open_price) or open_price <= 0:
                continue

            allocation = min(
                cash,
                INITIAL_CAPITAL * MAX_ALLOCATION
            )

            if allocation <= 0:
                continue

            buy_price = execution_buy(open_price)

            # Allocation sudah termasuk fee beli.
            quantity = allocation / (
                buy_price * (1 + FEE_RATE)
            )

            gross_buy = quantity * buy_price
            buy_fee = gross_buy * FEE_RATE
            total_buy_cost = gross_buy + buy_fee

            if total_buy_cost > cash:
                continue

            cash -= total_buy_cost

            positions[pair] = {
                "entry_time": timestamp,
                "buy_price": buy_price,
                "quantity": quantity,
                "buy_fee": buy_fee,
                "total_buy_cost": total_buy_cost
            }

        # ----------------------------------------------------
        # 3. UPDATE CANDLE SEBELUMNYA
        # ----------------------------------------------------

        for pair, row in current_rows.items():
            previous_rows[pair] = row

        # ----------------------------------------------------
        # 4. HITUNG EQUITY DENGAN ESTIMASI BIAYA LIKUIDASI
        # ----------------------------------------------------

        position_value = 0

        for pair, position in positions.items():
            df = data[pair]
            available = df.loc[:timestamp]

            if available.empty:
                continue

            close_price = available.iloc[-1]["Close"]

            if not np.isfinite(close_price) or close_price <= 0:
                continue

            estimated_sell_price = execution_sell(close_price)

            estimated_proceeds = (
                position["quantity"]
                * estimated_sell_price
                * (1 - FEE_RATE)
            )

            position_value += estimated_proceeds

        equity = cash + position_value

        equity_history.append({
            "Time": timestamp,
            "Cash": cash,
            "Position_Value": position_value,
            "Equity": equity,
            "Open_Positions": len(positions)
        })

    # ========================================================
    # 5. SIMPAN POSISI YANG MASIH TERBUKA
    # ========================================================

    for pair, position in positions.items():
        trades.append({
            "Pair": pair,
            "Entry_Time": position["entry_time"],
            "Exit_Time": pd.NaT,
            "Entry_Price": position["buy_price"],
            "Exit_Price": np.nan,
            "Quantity": position["quantity"],
            "Buy_Fee": position["buy_fee"],
            "Sell_Fee": np.nan,
            "Total_Fees": position["buy_fee"],
            "Net_PnL": np.nan,
            "Return_Percent": np.nan,
            "Exit_Type": "Still_Open"
        })

    # ========================================================
    # 6. METRIK HASIL
    # ========================================================

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_history)

    if equity_df.empty:
        raise ValueError("Equity history kosong. Periksa data indikator.")

    final_equity = equity_df.iloc[-1]["Equity"]
    total_return = (
        (final_equity / INITIAL_CAPITAL) - 1
    ) * 100

    equity_df["Peak"] = equity_df["Equity"].cummax()
    equity_df["Drawdown"] = (
        equity_df["Equity"] / equity_df["Peak"] - 1
    ) * 100

    max_drawdown = equity_df["Drawdown"].min()

    completed = trades_df[
        trades_df["Exit_Type"] == "Signal"
    ].copy()

    if not completed.empty:
        wins = completed[completed["Net_PnL"] > 0]
        losses = completed[completed["Net_PnL"] < 0]

        win_rate = len(wins) / len(completed) * 100

        gross_profit = wins["Net_PnL"].sum()
        gross_loss = abs(losses["Net_PnL"].sum())

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else np.inf
        )

        average_win = (
            wins["Net_PnL"].mean() if len(wins) else 0
        )

        average_loss = (
            losses["Net_PnL"].mean() if len(losses) else 0
        )

        total_fees = completed["Total_Fees"].sum()

    else:
        win_rate = 0
        profit_factor = 0
        average_win = 0
        average_loss = 0
        total_fees = 0

    elapsed_days = (
        equity_df.iloc[-1]["Time"] - equity_df.iloc[0]["Time"]
    ).total_seconds() / 86400

    if elapsed_days > 0 and final_equity > 0:
        cagr = (
            (final_equity / INITIAL_CAPITAL)
            ** (365.25 / elapsed_days) - 1
        ) * 100
    else:
        cagr = 0

    # ========================================================
    # 7. BTC BUY AND HOLD BENCHMARK
    # ========================================================

    btc_files = [
        df for pair, df in data.items()
        if pair == "BTCIDR"
    ]

    if btc_files:
        btc = btc_files[0]
        btc_start = btc.iloc[0]["Open"]
        btc_end = btc.iloc[-1]["Close"]

        btc_return = (
            (btc_end / btc_start) - 1
        ) * 100 if btc_start > 0 else np.nan
    else:
        btc_return = np.nan

    # ========================================================
    # 8. SIMPAN HASIL
    # ========================================================

    trades_path = os.path.join(
        OUTPUT_FOLDER, "trades_multi.csv"
    )

    equity_path = os.path.join(
        OUTPUT_FOLDER, "equity_multi.csv"
    )

    metrics_path = os.path.join(
        OUTPUT_FOLDER, "metrics_multi.csv"
    )

    trades_df.to_csv(trades_path, index=False)
    equity_df.to_csv(equity_path, index=False)

    metrics = {
        "Initial_Capital": INITIAL_CAPITAL,
        "Final_Equity": final_equity,
        "Total_Return_Percent": total_return,
        "CAGR_Percent": cagr,
        "Max_Drawdown_Percent": max_drawdown,
        "Completed_Trades": len(completed),
        "Open_Positions": len(positions),
        "Win_Rate_Percent": win_rate,
        "Profit_Factor": profit_factor,
        "Average_Win_Rp": average_win,
        "Average_Loss_Rp": average_loss,
        "Total_Trading_Fees_Rp": total_fees,
        "BTC_Buy_Hold_Return_Percent": btc_return,
        "Assumed_Fee_Per_Side": FEE_RATE,
        "Assumed_Full_Spread": FULL_SPREAD_RATE,
        "Assumed_Slippage_Per_Side": SLIPPAGE_RATE
    }

    pd.DataFrame(
        list(metrics.items()),
        columns=["Metric", "Value"]
    ).to_csv(metrics_path, index=False)

    # ========================================================
    # 9. TAMPILKAN RINGKASAN
    # ========================================================

    print("\n========== HASIL BACKTEST MULTI-PAIR ==========")
    print(f"Modal Awal          : Rp{INITIAL_CAPITAL:,.0f}")
    print(f"Equity Akhir        : Rp{final_equity:,.0f}")
    print(f"Total Return        : {total_return:.2f}%")
    print(f"CAGR                : {cagr:.2f}%")
    print(f"Max Drawdown        : {max_drawdown:.2f}%")
    print(f"Completed Trades    : {len(completed)}")
    print(f"Posisi Terbuka      : {len(positions)}")
    print(f"Win Rate            : {win_rate:.2f}%")
    print(f"Profit Factor       : {profit_factor:.4f}")
    print(f"Rata-rata Win       : Rp{average_win:,.0f}")
    print(f"Rata-rata Loss      : Rp{average_loss:,.0f}")
    print(f"Total Fee           : Rp{total_fees:,.0f}")
    print(f"BTC Buy & Hold      : {btc_return:.2f}%")

    print("\nFile hasil tersimpan:")
    print(trades_path)
    print(equity_path)
    print(metrics_path)

    print("\nCatatan: spread, slippage, dan fee adalah asumsi")
    print("simulasi, bukan data historis eksekusi aktual.")
    print("===============================================\n")


if __name__ == "__main__":
    run_backtest()
