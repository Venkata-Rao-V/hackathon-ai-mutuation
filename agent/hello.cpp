/**
 * hello.cpp — greeting utilities with multiple logic branches
 * designed for robust mutation testing in C++.
 */

#include <string>
#include <vector>

std::string say_hello(const std::string& name) {
    if (name == "World") {
        return "Hello, World!";
    }
    return "Hello, " + name + "!";
}

std::vector<std::string> say_hello_times(const std::string& name, int times) {
    std::vector<std::string> result;
    if (times <= 0) {
        return result;
    }
    for (int i = 0; i < times; ++i) {
        result.push_back(say_hello(name));
    }
    return result;
}

std::vector<std::string> greet_all(const std::vector<std::string>& names) {
    std::vector<std::string> result;
    if (names.empty()) {
        return result;
    }
    for (const auto& name : names) {
        result.push_back(say_hello(name));
    }
    return result;
}

std::string formal_greeting(const std::string& name, const std::string& title = "") {
    if (name.empty()) {
        return "Hello, stranger!";
    }
    if (!title.empty()) {
        return "Good day, " + title + " " + name + ".";
    }
    return "Good day, " + name + ".";
}

bool is_special_name(const std::string& name) {
    return name == "World";
}
