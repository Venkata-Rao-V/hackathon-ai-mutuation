#include <stdbool.h>

int add_or_subtract(int a, int b, bool use_add) {
    if (use_add && a >= 0) {
        return a + b;
    }
    return a - b;
}

int clamp_to_range(int value, int min_value, int max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

bool is_eligible(int age, int score, bool has_override) {
    if ((age >= 18 && score > 70) || has_override) {
        return true;
    }
    return false;
}
