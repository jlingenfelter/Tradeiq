"""Scenario modeling — pure math, stateless projection functions."""


def run_mortgage_payoff(
    balance: float,
    rate: float,
    monthly_payment: float,
    extra_payment: float = 0.0,
) -> dict:
    """Project mortgage payoff with optional extra payments.

    Args:
        balance: Current loan balance.
        rate: Annual interest rate as a percentage (e.g. 5.5 for 5.5%).
        monthly_payment: Required monthly payment.
        extra_payment: Additional monthly payment toward principal.
    """
    monthly_rate = rate / 100.0 / 12.0
    total_payment = monthly_payment + extra_payment

    # Standard payoff (no extra)
    std_projections = _amortize(balance, monthly_rate, monthly_payment)
    # Accelerated payoff (with extra)
    acc_projections = _amortize(balance, monthly_rate, total_payment)

    std_total_interest = sum(p["interest"] for p in std_projections)
    acc_total_interest = sum(p["interest"] for p in acc_projections)

    return {
        "projections": acc_projections,
        "summary": {
            "total_interest": round(acc_total_interest, 2),
            "months_saved": len(std_projections) - len(acc_projections),
            "interest_saved": round(std_total_interest - acc_total_interest, 2),
            "total_months": len(acc_projections),
            "standard_months": len(std_projections),
        },
    }


def _amortize(balance: float, monthly_rate: float, payment: float) -> list[dict]:
    """Run amortization schedule until balance is zero."""
    projections = []
    remaining = balance
    month = 0
    max_months = 600  # 50-year cap

    while remaining > 0.01 and month < max_months:
        month += 1
        interest = remaining * monthly_rate
        principal = min(payment - interest, remaining)
        if principal <= 0:
            # Payment doesn't cover interest — infinite loan
            break
        remaining -= principal
        remaining = max(0, remaining)
        projections.append({
            "month": month,
            "balance": round(remaining, 2),
            "interest": round(interest, 2),
            "principal": round(principal, 2),
        })

    return projections


def run_savings_projection(
    current: float,
    monthly_contribution: float,
    rate: float,
    months: int,
) -> dict:
    """Project savings growth with compound interest.

    Args:
        current: Current savings balance.
        monthly_contribution: Amount added each month.
        rate: Annual return rate as a percentage (e.g. 7.0 for 7%).
        months: Number of months to project.
    """
    monthly_rate = rate / 100.0 / 12.0
    projections = []
    value = current
    total_contributed = current

    for m in range(1, months + 1):
        growth = value * monthly_rate
        value += growth + monthly_contribution
        total_contributed += monthly_contribution
        projections.append({
            "month": m,
            "value": round(value, 2),
        })

    return {
        "projections": projections,
        "summary": {
            "final_value": round(value, 2),
            "total_contributed": round(total_contributed, 2),
            "total_growth": round(value - total_contributed, 2),
        },
    }


def run_asset_change(current_value: float, change_pct: float) -> dict:
    """Calculate the impact of an asset value change on net worth.

    Args:
        current_value: Current asset value.
        change_pct: Percentage change (e.g. -20 for a 20% drop, 15 for a 15% gain).
    """
    new_value = current_value * (1 + change_pct / 100.0)
    impact = new_value - current_value

    return {
        "new_value": round(new_value, 2),
        "impact": round(impact, 2),
    }


def run_debt_snowball(
    debts: list[dict],
    extra_budget: float,
) -> dict:
    """Project debt snowball payoff.

    Args:
        debts: List of dicts with {name, balance, rate, min_payment}.
        extra_budget: Extra monthly amount to throw at the smallest balance.
    """
    # Sort by balance ascending (snowball method)
    active_debts = sorted(
        [
            {
                "name": d["name"],
                "balance": float(d["balance"]),
                "rate": float(d["rate"]),
                "min_payment": float(d["min_payment"]),
            }
            for d in debts
        ],
        key=lambda x: x["balance"],
    )

    projections = []
    month = 0
    total_interest = 0.0
    max_months = 600
    freed_payments = 0.0  # min_payments from paid-off debts roll into next debt

    while any(d["balance"] > 0.01 for d in active_debts) and month < max_months:
        month += 1
        month_snapshot = {"month": month, "debts": []}

        # Determine target debt (smallest remaining balance)
        target_idx = None
        for i, d in enumerate(active_debts):
            if d["balance"] > 0.01:
                target_idx = i
                break

        for i, d in enumerate(active_debts):
            if d["balance"] <= 0.01:
                month_snapshot["debts"].append({"name": d["name"], "balance": 0.0})
                continue

            monthly_rate = d["rate"] / 100.0 / 12.0
            interest = d["balance"] * monthly_rate
            total_interest += interest

            payment = d["min_payment"]
            if i == target_idx:
                payment += extra_budget + freed_payments

            principal = min(payment - interest, d["balance"])
            if principal < 0:
                principal = 0
            d["balance"] = max(0, d["balance"] - principal)

            month_snapshot["debts"].append({
                "name": d["name"],
                "balance": round(d["balance"], 2),
            })

        # Check if any debt was just paid off this month, free its min_payment
        for d in active_debts:
            if d["balance"] <= 0.01 and d.get("_active", True):
                freed_payments += d["min_payment"]
                d["_active"] = False

        projections.append(month_snapshot)

    return {
        "projections": projections,
        "summary": {
            "months_to_free": month,
            "total_interest": round(total_interest, 2),
        },
    }
