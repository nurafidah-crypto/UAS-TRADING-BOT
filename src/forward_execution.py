
import time
from decimal import Decimal, ROUND_DOWN

from src.indodax import get_order_book
from src.forward_config import (
    FEE_RATE,
    PAIR_RULES,
    MAX_ORDERBOOK_AGE_SECONDS,
)


def failure(reason, retryable):
    return {
        "ok": False,
        "retryable": retryable,
        "reason": reason,
    }


def success(order):
    return {
        "ok": True,
        "retryable": False,
        "reason": None,
        "order": order,
    }


def round_quantity_down(pair, quantity):
    rules = PAIR_RULES[pair]
    increment = Decimal(str(rules["quantity_increment"]))
    amount = Decimal(str(quantity))

    rounded = (
        amount / increment
    ).to_integral_value(rounding=ROUND_DOWN) * increment

    return rounded


def get_valid_order_book(pair):
    if pair not in PAIR_RULES:
        return failure(
            f"Pair tidak terdaftar: {pair}",
            False
        )

    try:
        book = get_order_book(pair)
    except Exception as error:
        return failure(
            f"Gagal mengambil orderbook: {error}",
            True
        )

    if not book:
        return failure(
            "Orderbook tidak tersedia.",
            True
        )

    try:
        fetched_at = float(book["fetched_at"])
        age_seconds = time.time() - fetched_at

        if age_seconds < 0:
            return failure(
                "Timestamp orderbook tidak valid.",
                True
            )

        if age_seconds > MAX_ORDERBOOK_AGE_SECONDS:
            return failure(
                f"Orderbook kedaluwarsa: {age_seconds:.2f} detik.",
                True
            )

        bids = [
            (Decimal(str(price)), Decimal(str(amount)))
            for price, amount in book["bids"]
        ]

        asks = [
            (Decimal(str(price)), Decimal(str(amount)))
            for price, amount in book["asks"]
        ]

        bids = [
            level for level in bids
            if level[0] > 0 and level[1] > 0
        ]

        asks = [
            level for level in asks
            if level[0] > 0 and level[1] > 0
        ]

        if not bids or not asks:
            return failure(
                "Sisi bid atau ask kosong.",
                True
            )

        bids.sort(key=lambda item: item[0], reverse=True)
        asks.sort(key=lambda item: item[0])

        return {
            "ok": True,
            "bids": bids,
            "asks": asks,
            "fetched_at": fetched_at,
        }

    except (
        KeyError,
        TypeError,
        ValueError,
        ArithmeticError,
    ) as error:
        return failure(
            f"Format orderbook tidak valid: {error}",
            True
        )


def simulate_buy(pair, budget_idr):
    """
    Simulasi market BUY berdasarkan ASK.
    Budget sudah termasuk fee.
    """

    book = get_valid_order_book(pair)

    if not book["ok"]:
        return failure(
            book["reason"],
            book["retryable"]
        )

    try:
        budget = Decimal(str(budget_idr))
        fee_rate = Decimal(str(FEE_RATE))

        if budget <= 0:
            return failure(
                "Budget harus lebih besar dari nol.",
                False
            )

        rules = PAIR_RULES[pair]

        available_for_asset = (
            budget / (Decimal("1") + fee_rate)
        )

        remaining_idr = available_for_asset
        total_quantity = Decimal("0")

        for price, amount in book["asks"]:
            if remaining_idr <= 0:
                break

            level_cost = price * amount
            spend = min(remaining_idr, level_cost)
            quantity = spend / price

            total_quantity += quantity
            remaining_idr -= spend

        if remaining_idr > Decimal("0.000001"):
            return failure(
                "Depth ask tidak cukup untuk memenuhi budget.",
                True
            )

        quantity = round_quantity_down(
            pair,
            total_quantity
        )

        if quantity <= 0:
            return failure(
                "Kuantitas hasil pembulatan nol.",
                False
            )

        if quantity < Decimal(str(rules["min_quantity"])):
            return failure(
                "Kuantitas di bawah minimum order.",
                False
            )

        remaining_quantity = quantity
        actual_cost = Decimal("0")

        for price, amount in book["asks"]:
            if remaining_quantity <= 0:
                break

            filled = min(remaining_quantity, amount)
            actual_cost += filled * price
            remaining_quantity -= filled

        if remaining_quantity > 0:
            return failure(
                "Depth ask tidak cukup setelah pembulatan.",
                True
            )

        fee = actual_cost * fee_rate
        total_payment = actual_cost + fee

        if total_payment > budget:
            return failure(
                "Total biaya melebihi budget.",
                False
            )

        if actual_cost < Decimal(str(rules["min_idr"])):
            return failure(
                "Nilai order di bawah minimum IDR.",
                False
            )

        order = {
            "pair": pair,
            "side": "BUY",
            "quantity": float(quantity),
            "average_price": float(actual_cost / quantity),
            "gross_value": float(actual_cost),
            "fee": float(fee),
            "total_cost": float(total_payment),
        }

        return success(order)

    except (
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        return failure(
            f"Perhitungan BUY gagal: {error}",
            False
        )


def simulate_sell(pair, quantity_to_sell):
    """
    Simulasi market SELL berdasarkan BID.
    Seluruh kuantitas posisi harus dapat terjual.
    """

    book = get_valid_order_book(pair)

    if not book["ok"]:
        return failure(
            book["reason"],
            book["retryable"]
        )

    try:
        quantity = round_quantity_down(
            pair,
            quantity_to_sell
        )

        if quantity <= 0:
            return failure(
                "Kuantitas SELL tidak valid.",
                False
            )

        rules = PAIR_RULES[pair]

        if quantity < Decimal(str(rules["min_quantity"])):
            return failure(
                "Kuantitas posisi di bawah minimum SELL.",
                False
            )

        remaining_quantity = quantity
        gross_value = Decimal("0")

        for price, amount in book["bids"]:
            if remaining_quantity <= 0:
                break

            filled = min(remaining_quantity, amount)
            gross_value += filled * price
            remaining_quantity -= filled

        if remaining_quantity > 0:
            return failure(
                "Depth bid tidak cukup untuk menjual seluruh posisi.",
                True
            )

        fee = gross_value * Decimal(str(FEE_RATE))
        net_proceeds = gross_value - fee

        if gross_value < Decimal(str(rules["min_idr"])):
            return failure(
                "Nilai SELL di bawah minimum IDR.",
                False
            )

        order = {
            "pair": pair,
            "side": "SELL",
            "quantity": float(quantity),
            "average_price": float(gross_value / quantity),
            "gross_value": float(gross_value),
            "fee": float(fee),
            "net_proceeds": float(net_proceeds),
        }

        return success(order)

    except (
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        return failure(
            f"Perhitungan SELL gagal: {error}",
            False
        )
