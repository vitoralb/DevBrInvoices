import json
import os
from decimal import Decimal
from datetime import datetime


def load_tax_tables(tax_type=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if tax_type:
        json_path = os.path.join(base_dir, f"tax_tables_{tax_type}.json")
        if not os.path.exists(json_path):
            return []
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # if no tax_type, load all (for api_taxes_view maybe)
    data = []
    for f_name in os.listdir(base_dir):
        if f_name.startswith("tax_tables_") and f_name.endswith(".json"):
            with open(os.path.join(base_dir, f_name), "r", encoding="utf-8") as f:
                data.extend(json.load(f))
    return data


def parse_date(date_str):
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_active_table(tax_type, reference_date):
    tables = load_tax_tables(tax_type)
    valid_tables = []
    for t in tables:
        valid_from = parse_date(t.get("valid_from"))
        valid_to = parse_date(t.get("valid_to"))

        if valid_from <= reference_date:
            if valid_to is None or valid_to >= reference_date:
                valid_tables.append((valid_from, t))

    if not valid_tables:
        return None

    valid_tables.sort(key=lambda x: x[0], reverse=True)
    return valid_tables[0][1]


class TaxBracketModelSim:
    def __init__(self, data):
        self.min_value = Decimal(str(data.get("min_value", 0)))
        self.max_value = (
            Decimal(str(data["max_value"]))
            if data.get("max_value") is not None
            else None
        )
        self.nominal_rate = Decimal(str(data.get("nominal_rate", 0)))
        self.deduction = Decimal(str(data.get("deduction", 0)))
        self.cpp_allocation = Decimal(str(data.get("cpp_allocation", 0)))
        self.pis_allocation = Decimal(str(data.get("pis_allocation", 0)))
        self.cofins_allocation = Decimal(str(data.get("cofins_allocation", 0)))
        self.iss_allocation = Decimal(str(data.get("iss_allocation", 0)))


def get_applicable_bracket(tax_type, value, reference_date):
    table = get_active_table(tax_type, reference_date)
    if not table:
        raise ValueError(
            f"No active tax table found for {tax_type} on {reference_date}"
        )

    value = Decimal(str(value))
    brackets = table.get("brackets", [])
    brackets.sort(key=lambda b: Decimal(str(b.get("min_value", 0))))

    for b in brackets:
        min_v = Decimal(str(b.get("min_value", 0)))
        max_v = Decimal(str(b["max_value"])) if b.get("max_value") is not None else None

        if min_v <= value:
            if max_v is None or max_v >= value:
                return TaxBracketModelSim(b)

    # fallback
    for b in brackets:
        min_v = Decimal(str(b.get("min_value", 0)))
        max_v = b.get("max_value")
        if min_v <= value and max_v is None:
            return TaxBracketModelSim(b)

    raise ValueError(
        f"No applicable tax bracket found for {tax_type} with value {value} on {reference_date}"
    )


def get_minimum_salary(reference_date):
    table = get_active_table("INSS", reference_date)
    if not table:
        raise ValueError(
            f"No active INSS tax table found for {reference_date} to determine minimum salary."
        )

    brackets = table.get("brackets", [])
    brackets.sort(key=lambda b: Decimal(str(b.get("min_value", 0))))

    lowest_bracket = brackets[0]
    if lowest_bracket.get("max_value") is None:
        raise ValueError(
            f"Invalid INSS table configuration for {reference_date}: missing lowest bracket max_value."
        )

    return Decimal(str(lowest_bracket["max_value"]))


def calculate_inss(pro_labore_amount, reference_date):
    table = get_active_table("INSS", reference_date)
    if not table:
        raise ValueError(f"No active tax table found for INSS on {reference_date}")

    brackets = table.get("brackets", [])
    brackets.sort(key=lambda b: Decimal(str(b.get("min_value", 0))), reverse=True)

    if not brackets:
        raise ValueError(
            f"No applicable INSS bracket found for {pro_labore_amount} on {reference_date}"
        )

    top_bracket = TaxBracketModelSim(brackets[0])
    ceiling = top_bracket.max_value if top_bracket.max_value else top_bracket.min_value

    amount = Decimal(str(pro_labore_amount))
    base_calc = min(amount, ceiling)
    inss = base_calc * Decimal("0.11")

    from decimal import ROUND_HALF_UP

    return max(Decimal("0.00"), inss).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
