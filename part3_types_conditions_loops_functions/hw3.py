#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

NUM_IN_DATA = 3
MONTH_CNT = 12
FEB_NUM = 2
LEN_OTHER_OF_YEAR = 2
LEN_YEAR = 4
LEN_CATEGORY = 2
COST_CMD_LEN = 4
THIRTY_DAY_MONTHS = (4, 6, 9, 11)
DATE_PART_LENGTHS = (LEN_OTHER_OF_YEAR, LEN_OTHER_OF_YEAR, LEN_YEAR)
CATEGORY_SEPARATOR = "::"
MINUS_SIGN = "-"
DECIMAL_POINT = "."
AMOUNT_KEY = "amount"
DATE_KEY = "date"
CATEGORY_KEY = "category"
CAPITAL_KEY = "capital"
INCOME_KEY = "income"
EXPENSES_KEY = "expenses"
CATEGORIES_KEY = "categories"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

Date = tuple[int, int, int]
AmountParts = tuple[str, str, int]

financial_transactions_storage: list[dict[str, Any]] = []


def get_expense_categories() -> dict[str, tuple[str, ...]]:
    return dict(EXPENSE_CATEGORIES)


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def is_int(value: str) -> bool:
    if not value:
        return False
    if value[0] != MINUS_SIGN:
        return value.isdigit()
    if len(value) == 1:
        return False
    return value[1:].isdigit()


def has_valid_date_lengths(parts: list[str]) -> bool:
    return (
        len(parts[0]) == DATE_PART_LENGTHS[0]
        and len(parts[1]) == DATE_PART_LENGTHS[1]
        and len(parts[2]) == DATE_PART_LENGTHS[2]
    )


def get_max_day(month: int, year: int) -> int:
    if month == FEB_NUM:
        return 29 if is_leap_year(year) else 28
    if month in THIRTY_DAY_MONTHS:
        return 30
    return 31


def extract_date(maybe_dt: str) -> Date | None:
    parts = maybe_dt.split(MINUS_SIGN)
    if len(parts) != NUM_IN_DATA or not has_valid_date_lengths(parts):
        return None

    day, month, year = map(int, parts)
    if month < 1 or month > MONTH_CNT or day < 1:
        return None
    if day > get_max_day(month, year):
        return None
    return day, month, year


def income_handler(amount: float, income_date: str) -> str:
    date = extract_date(income_date)
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({AMOUNT_KEY: amount, DATE_KEY: date})
    return OP_SUCCESS_MSG


def is_category_exist(category: str) -> bool:
    parts = category.split(CATEGORY_SEPARATOR)
    categories = get_expense_categories()
    if len(parts) != LEN_CATEGORY:
        return False
    main_category, sub_category = parts
    return main_category in categories and sub_category in categories[main_category]


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date = extract_date(income_date)
    status = OP_SUCCESS_MSG

    if not is_category_exist(category_name):
        status = NOT_EXISTS_CATEGORY
    elif amount <= 0:
        status = NONPOSITIVE_VALUE_MSG
    elif date is None:
        status = INCORRECT_DATE_MSG

    if status == OP_SUCCESS_MSG:
        financial_transactions_storage.append(
            {CATEGORY_KEY: category_name, AMOUNT_KEY: amount, DATE_KEY: date},
        )
    else:
        financial_transactions_storage.append({})
    return status


def cost_categories_handler() -> str:
    categories: list[str] = []
    for main_category, sub_categories in EXPENSE_CATEGORIES.items():
        categories.extend(
            f"{main_category}{CATEGORY_SEPARATOR}{sub_category}"
            for sub_category in sub_categories
        )
    return "\n".join(categories)


def is_after_report(date: Date, report: Date) -> bool:
    if date[2] != report[2]:
        return date[2] > report[2]
    if date[1] != report[1]:
        return date[1] > report[1]
    return date[0] > report[0]


def is_same_month(date: Date, report: Date) -> bool:
    if date[1] != report[1]:
        return False
    return date[2] == report[2]


def update_categories(
    categories: dict[str, float],
    category_name: str,
    amount: float,
) -> None:
    category = category_name.split(CATEGORY_SEPARATOR)[1]
    categories[category] = categories.get(category, 0) + amount


def build_month_result(diff: float) -> str:
    result_name = "profit" if diff >= 0 else "loss"
    return f"This month, the {result_name} amounted to {abs(diff):.2f} rubles."


def build_stats_header(report_date: str, stats: dict[str, Any], diff: float) -> list[str]:
    return [
        f"Your statistics as of {report_date}:",
        f"Total capital: {stats[CAPITAL_KEY]:.2f} rubles",
        build_month_result(diff),
        f"Income: {stats[INCOME_KEY]:.2f} rubles",
        f"Expenses: {stats[EXPENSES_KEY]:.2f} rubles",
        "",
        "Details (category: amount):",
    ]


def make_stats() -> dict[str, Any]:
    return {
        CAPITAL_KEY: 0,
        INCOME_KEY: 0,
        EXPENSES_KEY: 0,
        CATEGORIES_KEY: {},
    }


def update_capital(stats: dict[str, Any], transaction: dict[str, Any]) -> None:
    amount = transaction[AMOUNT_KEY]
    if CATEGORY_KEY in transaction:
        stats[CAPITAL_KEY] -= amount
        return
    stats[CAPITAL_KEY] += amount


def update_month_stats(stats: dict[str, Any], transaction: dict[str, Any]) -> None:
    amount = transaction[AMOUNT_KEY]
    category_name = transaction.get(CATEGORY_KEY)
    if category_name is not None:
        stats[EXPENSES_KEY] += amount
        categories = stats[CATEGORIES_KEY]
        update_categories(categories, category_name, amount)
        return
    stats[INCOME_KEY] += amount


def calculate_stats(report: Date) -> dict[str, Any]:
    stats = make_stats()
    for transaction in financial_transactions_storage:
        if not transaction:
            continue
        if is_after_report(transaction[DATE_KEY], report):
            continue
        update_capital(stats, transaction)
        if is_same_month(transaction[DATE_KEY], report):
            update_month_stats(stats, transaction)
    return stats


def build_stats_details(categories: dict[str, float]) -> list[str]:
    return [
        f"{index}. {category}: {amount:.2f}"
        for index, (category, amount) in enumerate(sorted(categories.items()), 1)
    ]


def format_stats(report_date: str, stats: dict[str, Any]) -> str:
    diff = stats[INCOME_KEY] - stats[EXPENSES_KEY]
    lines = build_stats_header(report_date, stats, diff)
    lines.extend(build_stats_details(stats[CATEGORIES_KEY]))
    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    report = extract_date(report_date)
    if report is None:
        return INCORRECT_DATE_MSG

    stats = calculate_stats(report)
    return format_stats(report_date, stats)


def is_valid_amount_symbol(symbol: str, left: str, *, in_fraction: bool) -> bool:
    if symbol.isdigit():
        return True
    return symbol == MINUS_SIGN and left == "" and not in_fraction


def split_amount_parts(amount_str: str) -> AmountParts | None:
    dot_count = 0
    left = ""
    right = ""
    in_fraction = False

    for symbol in amount_str:
        if symbol == DECIMAL_POINT:
            dot_count += 1
            in_fraction = True
            continue
        if not is_valid_amount_symbol(symbol, left, in_fraction=in_fraction):
            return None
        if in_fraction:
            right += symbol
        else:
            left += symbol

    return left, right, dot_count


def normalize_amount_parts(parts: AmountParts) -> AmountParts | None:
    left, right, dot_count = parts
    if dot_count > 1:
        return None
    if left == MINUS_SIGN or (left == "" and right == ""):
        return None

    left = left or "0"
    right = right or "0"
    if dot_count == 0 and not is_int(left):
        return None
    return left, right, dot_count


def parse_amount(amount_str: str) -> float | None:
    parts = split_amount_parts(amount_str.replace(",", DECIMAL_POINT))
    if parts is None:
        return None

    normalized = normalize_amount_parts(parts)
    if normalized is None:
        return None

    left, right, dot_count = normalized
    if dot_count == 0:
        return float(left)
    return float(f"{left}.{right}")


def get_indexes(parts: list[str]) -> tuple[int, int]:
    command = parts[0]
    if command == "income" and len(parts) == NUM_IN_DATA:
        return 1, 2
    if command == "cost" and len(parts) == COST_CMD_LEN:
        return 2, 3
    return -1, -1


def is_cost_categories_command(parts: list[str]) -> bool:
    if len(parts) != LEN_CATEGORY:
        return False
    if parts[0] != "cost":
        return False
    return parts[1] == "categories"


def amount_command(parts: list[str], amount_index: int, date_index: int) -> str:
    amount = parse_amount(parts[amount_index])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG
    if parts[0] == "income":
        return income_handler(amount, parts[date_index])

    result = cost_handler(parts[1], amount, parts[date_index])
    if result == NOT_EXISTS_CATEGORY:
        return f"{result}\n{cost_categories_handler()}"
    return result


def main() -> None:
    parts = input().split()
    if not parts:
        print(UNKNOWN_COMMAND_MSG)
        return

    command = parts[0]
    if is_cost_categories_command(parts):
        print(cost_categories_handler())
        return
    if command == "stats" and len(parts) == LEN_CATEGORY:
        print(stats_handler(parts[1]))
        return

    amount_index, date_index = get_indexes(parts)
    if amount_index != -1:
        print(amount_command(parts, amount_index, date_index))
        return
    print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
