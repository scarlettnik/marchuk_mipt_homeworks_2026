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

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": (),
}


financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    return (year % 400 == 0) or (year % 4 == 0 and year % 100 != 0)


def is_int(value: str) -> bool:
    if not value:
        return False

    if value[0] != "-":
        return value.isdigit()

    if len(value) == 1:
        return False

    return value[1:].isdigit()


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != NUM_IN_DATA:
        return None
    if len(parts[0]) != LEN_OTHER_OF_YEAR or len(parts[1]) != LEN_OTHER_OF_YEAR or len(parts[2]) != LEN_YEAR:
        return None

    day, month, year = map(int, parts)
    if month < 1 or month > MONTH_CNT or day < 1:
        return None
    if month == FEB_NUM:
        max_day = 29 if is_leap_year(year) else 28
    elif month in (4, 6, 9, 11):
        max_day = 30
    else:
        max_day = 31
    return (day, month, year) if day <= max_day else None


def income_handler(amount: float, income_date: str) -> str:
    date = extract_date(income_date)
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({"amount": amount, "date": date})
    return OP_SUCCESS_MSG


def is_category_exist(category: str) -> bool:
    parts = category.split("::")
    if len(parts) != LEN_CATEGORY:
        return False
    main_category, sub_category = parts
    return main_category in EXPENSE_CATEGORIES and sub_category in EXPENSE_CATEGORIES[main_category]


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date = extract_date(income_date)
    if not is_category_exist(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    categories: list[str] = []

    for main_cat, sub_cats in EXPENSE_CATEGORIES.items():
        categories.extend(f"{main_cat}::{sub_cat}" for sub_cat in sub_cats)

    return "\n".join(categories)


def stats_handler(report_date: str) -> str:
    report = extract_date(report_date)
    if report is None:
        return INCORRECT_DATE_MSG

    capital = 0.0
    income = 0.0
    expenses = 0.0
    categories: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if not transaction:
            continue

        date = transaction["date"]
        if (
            date[2],
            date[1],
            date[0],
        ) > (
            report[2],
            report[1],
            report[0],
        ):
            continue

        amount = transaction["amount"]
        is_cost = "category" in transaction

        if is_cost:
            capital -= amount
        else:
            capital += amount

        if date[1] != report[1] or date[2] != report[2]:
            continue

        if is_cost:
            expenses += amount
            category = transaction["category"].split("::")[1]
            categories[category] = categories.get(category, 0.0) + amount
        else:
            income += amount

    diff = income - expenses

    result = (
        f"Your statistics as of {report_date}:\n"
        f"Total capital: {capital:.2f} rubles\n"
        f"This month, the {'profit' if diff >= 0 else 'loss'} amounted to {abs(diff):.2f} rubles.\n"
        f"Income: {income:.2f} rubles\n"
        f"Expenses: {expenses:.2f} rubles\n\n"
        "Details (category: amount):"
    )

    for i, (category, amount) in enumerate(sorted(categories.items()), 1):
        result += f"\n{i}. {category}: {amount:.2f}"

    return result


def parse_amount(amount_str: str) -> float | None:
    amount_str = amount_str.replace(",", ".")
    dot_count = 0
    left = ""
    right = ""
    in_fraction = False

    for symbol in amount_str:
        if symbol == ".":
            dot_count += 1
            in_fraction = True
            continue

        if not symbol.isdigit() and not (symbol == "-" and left == "" and not in_fraction):
            return None

        if in_fraction:
            right += symbol
        else:
            left += symbol

    if dot_count > 1:
        return None
    if left == "-" or (left == "" and right == ""):
        return None
    if left == "":
        left = "0"
    if right == "":
        right = "0"
    if dot_count == 0 and not is_int(left):
        return None

    return float(left) if dot_count == 0 else float(left + "." + right)


def main() -> None:
    parts = input().split()

    if not parts:
        print(UNKNOWN_COMMAND_MSG)
        return

    result = UNKNOWN_COMMAND_MSG
    command = parts[0]

    if command == "income" and len(parts) == NUM_IN_DATA:
        amount_index = 1
        date_index = 2
    elif command == "cost" and len(parts) == COST_CMD_LEN:
        amount_index = 2
        date_index = 3
    else:
        amount_index = -1
        date_index = -1

    if command == "cost" and parts[1] == "categories" and len(parts) == LEN_CATEGORY:
        result = cost_categories_handler()
    elif command == "stats" and len(parts) == LEN_CATEGORY:
        result = stats_handler(parts[1])
    elif amount_index != -1:
        amount = parse_amount(parts[amount_index])
        if amount is None:
            result = NONPOSITIVE_VALUE_MSG
        elif command == "income":
            result = income_handler(amount, parts[date_index])
        else:
            result = cost_handler(parts[1], amount, parts[date_index])
            if result == NOT_EXISTS_CATEGORY:
                result += "\n" + cost_categories_handler()

    print(result)


if __name__ == "__main__":
    main()
