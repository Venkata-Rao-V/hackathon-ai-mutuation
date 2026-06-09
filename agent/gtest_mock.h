/**
 * gtest_mock.h — A dependency-free, high-performance lightweight GoogleTest mock harness
 * designed to run on any platform (Windows, macOS, Linux) with standard g++ compiler environments.
 */

#ifndef GTEST_MOCK_H
#define GTEST_MOCK_H

#include <iostream>
#include <vector>
#include <string>
#include <functional>
#include <stdexcept>

struct TestCase {
    std::string suite;
    std::string name;
    std::function<void()> fn;
};

inline std::vector<TestCase>& getTestCases() {
    static std::vector<TestCase> testCases;
    return testCases;
}

struct RegisterTest {
    RegisterTest(const std::string& suite, const std::string& name, std::function<void()> fn) {
        getTestCases().push_back({suite, name, fn});
    }
};

#define TEST(suite, name) \
    void suite##_##name##_impl(); \
    static RegisterTest suite##_##name##_reg(#suite, #name, suite##_##name##_impl); \
    void suite##_##name##_impl()

#define EXPECT_EQ(val1, val2) \
    if ((val1) != (val2)) { \
        std::cerr << "[ FAILED ] EXPECT_EQ failed at line " << __LINE__ << std::endl; \
        std::cerr << "  Expected: " << (val2) << " but got: " << (val1) << std::endl; \
        throw std::runtime_error("FAIL"); \
    }

#define EXPECT_TRUE(val) \
    if (!(val)) { \
        std::cerr << "[ FAILED ] EXPECT_TRUE failed at line " << __LINE__ << std::endl; \
        throw std::runtime_error("FAIL"); \
    }

#define EXPECT_FALSE(val) \
    if (val) { \
        std::cerr << "[ FAILED ] EXPECT_FALSE failed at line " << __LINE__ << std::endl; \
        throw std::runtime_error("FAIL"); \
    }

#endif
