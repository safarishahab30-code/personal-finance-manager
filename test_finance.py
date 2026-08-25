from auth import check_password_strength
from transactions import generate_transaction_id, validate_amount


def calculate_balance(transactions):
    income = sum(t["amount"] for t in transactions if t.get("type") == "income")
    expense = sum(
        t["amount"] for t in transactions if t.get("type") == "expense"
    )
    return income, expense, income - expense


def get_user_transactions(transactions, username):
    return [t for t in transactions if t.get("username") == username]


def test_calculate_balance_with_data():
    sample = [
        {"type": "income", "amount": 50000},
        {"type": "expense", "amount": 20000},
        {"type": "expense", "amount": 10000},
    ]
    inc, exp, net = calculate_balance(sample)
    assert inc == 50000
    assert exp == 30000
    assert net == 20000


def test_calculate_balance_empty():
    inc, exp, net = calculate_balance([])
    assert inc == 0
    assert exp == 0
    assert net == 0


def test_validate_amount_valid():
    assert validate_amount("50000") == 50000


def test_validate_amount_negative_or_zero():
    assert validate_amount("-1000") is None
    assert validate_amount("0") is None


def test_validate_amount_invalid_string():
    assert validate_amount("abc") is None


def test_generate_transaction_id_empty_list():
    assert generate_transaction_id([]) == 1


def test_generate_transaction_id_incremental():
    data = [{"id": 1}, {"id": 2}, {"id": 5}]
    assert generate_transaction_id(data) == 6


def test_get_user_transactions_filtering():
    all_data = [
        {"id": 1, "username": "shahab", "amount": 1000},
        {"id": 2, "username": "mamad", "amount": 2000},
        {"id": 3, "username": "shahab", "amount": 3000},
    ]
    shahab_txs = get_user_transactions(all_data, "shahab")
    assert len(shahab_txs) == 2
    assert [t["id"] for t in shahab_txs] == [1, 3]


def test_get_user_transactions_not_found():
    all_data = [{"id": 1, "username": "mamad", "amount": 2000}]
    assert get_user_transactions(all_data, "shahab") == []


def test_password_strength():
    assert check_password_strength("123")[0] is False
    assert check_password_strength("abcdef")[0] is False
    assert check_password_strength("123456")[0] is False
    assert check_password_strength("Pass123")[0] is True
