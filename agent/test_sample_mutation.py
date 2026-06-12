import sample_mutation


def test_arithmetic_substitution_add_path():
    assert sample_mutation.arithmetic_substitution(8, 3, True) == 11


def test_arithmetic_substitution_subtract_path():
    assert sample_mutation.arithmetic_substitution(8, 3, False) == 5


def test_relational_boundary_low_mid_high():
    assert sample_mutation.relational_boundary(9) == "LOW"
    assert sample_mutation.relational_boundary(10) == "MID"
    assert sample_mutation.relational_boundary(20) == "MID"
    assert sample_mutation.relational_boundary(21) == "HIGH"


def test_boolean_inversion_truth_table():
    assert sample_mutation.boolean_inversion(True, False) is True
    assert sample_mutation.boolean_inversion(True, True) is False
    assert sample_mutation.boolean_inversion(False, False) is False


def test_return_value_stripping_behavior():
    assert sample_mutation.return_value_stripping(2) == 1
    assert sample_mutation.return_value_stripping(0) == 0
