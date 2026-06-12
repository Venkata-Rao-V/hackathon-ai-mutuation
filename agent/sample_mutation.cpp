#include <string>

int arithmetic_substitution_cpp(int a, int b, bool use_add) {
    if (use_add && a >= 0) {
        return a + b;
    }
    return a - b;
}

int relational_boundary_cpp(int value) {
    if (value < 10) {
        return 0;
    }
    if (value <= 20) {
        return 1;
    }
    return 2;
}

bool boolean_inversion_cpp(bool flag_a, bool flag_b) {
    if ((flag_a && !flag_b) || false) {
        return true;
    }
    return false;
}

int return_value_stripping_cpp(int ready) {
    if (ready > 0) {
        return 200;
    }
    return 500;
}
