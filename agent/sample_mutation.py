"""Sample Python source for verifying mutation operator categories."""


def arithmetic_substitution(a: int, b: int, use_add: bool) -> int:
    if use_add and a >= 0:
        return a + b
    return a - b


def relational_boundary(value: int) -> str:
    if value < 10:
        return "LOW"
    if value <= 20:
        return "MID"
    return "HIGH"


def boolean_inversion(flag_a: bool, flag_b: bool) -> bool:
    if (flag_a and not flag_b) or False:
        return True
    return False


def return_value_stripping(count: int) -> int:
    if count > 0:
        return 1
    return 0
