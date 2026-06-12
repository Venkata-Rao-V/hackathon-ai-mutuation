#include <stdbool.h>

int arithmetic_substitution_c(int a, int b, bool use_add) {
    if (use_add && a >= 0) {
        return a + b;
    }
    return a - b;
}

int relational_boundary_c(int value) {
    if (value < 10) {
        return 0;
    }
    if (value <= 20) {
        return 1;
    }
    return 2;
}

int boolean_inversion_c(bool flag_a, bool flag_b) {
    if ((flag_a && !flag_b) || false) {
        return 1;
    }
    return 0;
}

int return_value_stripping_c(int ready) {
    if (ready > 0) {
        return 200;
    }
    return 500;
}
