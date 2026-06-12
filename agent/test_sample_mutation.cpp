#include "gtest_mock.h"

int arithmetic_substitution_cpp(int a, int b, bool use_add);
int relational_boundary_cpp(int value);
bool boolean_inversion_cpp(bool flag_a, bool flag_b);
int return_value_stripping_cpp(int ready);

TEST(TestSampleMutationCpp, ArithmeticSubstitution) {
    EXPECT_EQ(arithmetic_substitution_cpp(8, 3, true), 11);
    EXPECT_EQ(arithmetic_substitution_cpp(8, 3, false), 5);
}

TEST(TestSampleMutationCpp, RelationalBoundary) {
    EXPECT_EQ(relational_boundary_cpp(9), 0);
    EXPECT_EQ(relational_boundary_cpp(10), 1);
    EXPECT_EQ(relational_boundary_cpp(20), 1);
    EXPECT_EQ(relational_boundary_cpp(21), 2);
}

TEST(TestSampleMutationCpp, BooleanInversion) {
    EXPECT_TRUE(boolean_inversion_cpp(true, false));
    EXPECT_FALSE(boolean_inversion_cpp(true, true));
    EXPECT_FALSE(boolean_inversion_cpp(false, false));
}

TEST(TestSampleMutationCpp, ReturnValueStripping) {
    EXPECT_EQ(return_value_stripping_cpp(1), 200);
    EXPECT_EQ(return_value_stripping_cpp(0), 500);
}

int main() {
    int passed = 0;
    int failed = 0;
    auto& cases = getTestCases();
    std::cout << "[==========] Running " << cases.size() << " tests." << std::endl;
    for (auto& tc : cases) {
        std::cout << "[ RUN      ] " << tc.suite << "." << tc.name << std::endl;
        try {
            tc.fn();
            std::cout << "[       OK ] " << tc.suite << "." << tc.name << std::endl;
            passed++;
        } catch (...) {
            std::cout << "[  FAILED  ] " << tc.suite << "." << tc.name << std::endl;
            failed++;
        }
    }
    std::cout << "[  PASSED  ] " << passed << " tests." << std::endl;
    if (failed > 0) {
        std::cout << "[  FAILED  ] " << failed << " tests." << std::endl;
        return 1;
    }
    return 0;
}
