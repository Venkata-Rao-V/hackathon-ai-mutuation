/**
 * test_hello.cpp — C++ GoogleTest specification suite for hello.cpp
 */

#include "gtest_mock.h"
#include <string>
#include <vector>

// Forward declarations of hello.cpp functions
std::string say_hello(const std::string& name);
std::vector<std::string> say_hello_times(const std::string& name, int times);
std::vector<std::string> greet_all(const std::vector<std::string>& names);
std::string formal_greeting(const std::string& name, const std::string& title);
bool is_special_name(const std::string& name);

// ─────────────────────────────────────────────────────────────
// say_hello Tests
// ─────────────────────────────────────────────────────────────

TEST(TestSayHello, WorldSpecialCase) {
    EXPECT_EQ(say_hello("World"), "Hello, World!");
}

TEST(TestSayHello, RegularName) {
    EXPECT_EQ(say_hello("Alice"), "Hello, Alice!");
}

TEST(TestSayHello, EmptyString) {
    EXPECT_EQ(say_hello(""), "Hello, !");
}

TEST(TestSayHello, IsSpecialNameTrue) {
    EXPECT_TRUE(is_special_name("World"));
}

TEST(TestSayHello, IsSpecialNameFalse) {
    EXPECT_FALSE(is_special_name("Alice"));
}

// ─────────────────────────────────────────────────────────────
// say_hello_times Tests
// ─────────────────────────────────────────────────────────────

TEST(TestSayHelloTimes, ZeroTimesReturnsEmpty) {
    auto res = say_hello_times("Alice", 0);
    EXPECT_TRUE(res.empty());
}

TEST(TestSayHelloTimes, NegativeTimesReturnsEmpty) {
    auto res = say_hello_times("Alice", -3);
    EXPECT_TRUE(res.empty());
}

TEST(TestSayHelloTimes, ThreeTimes) {
    auto res = say_hello_times("Alice", 3);
    EXPECT_EQ(res.size(), static_cast<size_t>(3));
    EXPECT_EQ(res[0], "Hello, Alice!");
    EXPECT_EQ(res[1], "Hello, Alice!");
    EXPECT_EQ(res[2], "Hello, Alice!");
}

// ─────────────────────────────────────────────────────────────
// formal_greeting Tests
// ─────────────────────────────────────────────────────────────

TEST(TestFormalGreeting, NoName) {
    EXPECT_EQ(formal_greeting("", "Dr."), "Hello, stranger!");
}

TEST(TestFormalGreeting, WithTitle) {
    EXPECT_EQ(formal_greeting("Alice", "Dr."), "Good day, Dr. Alice.");
}

TEST(TestFormalGreeting, WithoutTitle) {
    EXPECT_EQ(formal_greeting("Alice", ""), "Good day, Alice.");
}

// ─────────────────────────────────────────────────────────────
// Main entrypoint runner that behaves like GoogleTest executable
// ─────────────────────────────────────────────────────────────

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
        } catch (const std::exception& e) {
            std::cout << "[  FAILED  ] " << tc.suite << "." << tc.name << " with exception: " << e.what() << std::endl;
            failed++;
        } catch (...) {
            std::cout << "[  FAILED  ] " << tc.suite << "." << tc.name << std::endl;
            failed++;
        }
    }
    std::cout << "[==========] Test results count summary" << std::endl;
    std::cout << "[  PASSED  ] " << passed << " tests." << std::endl;
    if (failed > 0) {
        std::cout << "[  FAILED  ] " << failed << " tests." << std::endl;
        return 1;
    }
    return 0;
}
