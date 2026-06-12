#include <assert.h>
#include <stdbool.h>

int add_or_subtract(int a, int b, bool use_add);
int clamp_to_range(int value, int min_value, int max_value);
bool is_eligible(int age, int score, bool has_override);

static void test_add_or_subtract(void) {
    assert(add_or_subtract(10, 3, true) == 13);
    assert(add_or_subtract(10, 3, false) == 7);
}

static void test_clamp_to_range(void) {
    assert(clamp_to_range(5, 0, 10) == 5);
    assert(clamp_to_range(-2, 0, 10) == 0);
    assert(clamp_to_range(11, 0, 10) == 10);
}

static void test_is_eligible(void) {
    assert(is_eligible(21, 75, false) == true);
    assert(is_eligible(17, 75, false) == false);
    assert(is_eligible(17, 50, true) == true);
}

int main(void) {
    test_add_or_subtract();
    test_clamp_to_range();
    test_is_eligible();
    return 0;
}
