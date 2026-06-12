#include <assert.h>
#include <stdbool.h>

int arithmetic_substitution_c(int a, int b, bool use_add);
int relational_boundary_c(int value);
int boolean_inversion_c(bool flag_a, bool flag_b);
int return_value_stripping_c(int ready);

static void test_arithmetic_substitution_c(void) {
    assert(arithmetic_substitution_c(8, 3, true) == 11);
    assert(arithmetic_substitution_c(8, 3, false) == 5);
}

static void test_relational_boundary_c(void) {
    assert(relational_boundary_c(9) == 0);
    assert(relational_boundary_c(10) == 1);
    assert(relational_boundary_c(20) == 1);
    assert(relational_boundary_c(21) == 2);
}

static void test_boolean_inversion_c(void) {
    assert(boolean_inversion_c(true, false) == 1);
    assert(boolean_inversion_c(true, true) == 0);
    assert(boolean_inversion_c(false, false) == 0);
}

static void test_return_value_stripping_c(void) {
    assert(return_value_stripping_c(1) == 200);
    assert(return_value_stripping_c(0) == 500);
}

int main(void) {
    test_arithmetic_substitution_c();
    test_relational_boundary_c();
    test_boolean_inversion_c();
    test_return_value_stripping_c();
    return 0;
}
