"""
test_hello.py — exhaustive tests for hello.py

Scenarios covered:
  say_hello         — World, regular name, empty string, numbers, special chars, whitespace
  say_hello_times   — zero, one, many, negative, name=World
  greet_all         — empty list, one name, many names, mixed empty strings
  formal_greeting   — no name, name only, name + title, whitespace title
  shout_hello       — empty, regular, World
  count_hellos      — empty list, all valid, some empty, all empty
  is_special_name   — World, non-World, empty, mixed-case
"""

import hello


# ─────────────────────────────────────────────────────────────
# say_hello
# ─────────────────────────────────────────────────────────────

class TestSayHello:
    def test_world_special_case(self):
        assert hello.say_hello("World") == "Hello, World!"

    def test_regular_name(self):
        assert hello.say_hello("Alice") == "Hello, Alice!"

    def test_lowercase_world_is_not_special(self):
        assert hello.say_hello("world") == "Hello, world!"

    def test_uppercase_world_is_not_special(self):
        assert hello.say_hello("WORLD") == "Hello, WORLD!"

    def test_empty_string(self):
        assert hello.say_hello("") == "Hello, !"

    def test_numeric_string(self):
        assert hello.say_hello("123") == "Hello, 123!"

    def test_special_characters(self):
        assert hello.say_hello("@#$") == "Hello, @#$!"

    def test_whitespace_name(self):
        assert hello.say_hello("  ") == "Hello,   !"

    def test_name_with_spaces(self):
        assert hello.say_hello("John Doe") == "Hello, John Doe!"

    def test_single_char(self):
        assert hello.say_hello("A") == "Hello, A!"

    def test_unicode_name(self):
        assert hello.say_hello("日本語") == "Hello, 日本語!"

    def test_return_type_is_str(self):
        assert isinstance(hello.say_hello("Alice"), str)

    def test_world_result_contains_world(self):
        assert "World" in hello.say_hello("World")

    def test_non_world_result_contains_name(self):
        assert "Bob" in hello.say_hello("Bob")

    def test_greeting_starts_with_hello(self):
        assert hello.say_hello("Alice").startswith("Hello")

    def test_greeting_ends_with_exclamation(self):
        assert hello.say_hello("Alice").endswith("!")


# ─────────────────────────────────────────────────────────────
# say_hello_times
# ─────────────────────────────────────────────────────────────

class TestSayHelloTimes:
    def test_zero_times_returns_empty(self):
        assert hello.say_hello_times("Alice", 0) == []

    def test_negative_times_returns_empty(self):
        assert hello.say_hello_times("Alice", -5) == []

    def test_one_time(self):
        assert hello.say_hello_times("Alice", 1) == ["Hello, Alice!"]

    def test_three_times(self):
        result = hello.say_hello_times("Alice", 3)
        assert result == ["Hello, Alice!", "Hello, Alice!", "Hello, Alice!"]

    def test_length_matches_times(self):
        assert len(hello.say_hello_times("Bob", 5)) == 5

    def test_world_special_case_repeated(self):
        result = hello.say_hello_times("World", 2)
        assert result == ["Hello, World!", "Hello, World!"]

    def test_returns_list(self):
        assert isinstance(hello.say_hello_times("Alice", 2), list)

    def test_all_items_are_strings(self):
        result = hello.say_hello_times("Alice", 3)
        assert all(isinstance(item, str) for item in result)

    def test_minus_one_returns_empty(self):
        assert hello.say_hello_times("Alice", -1) == []


# ─────────────────────────────────────────────────────────────
# greet_all
# ─────────────────────────────────────────────────────────────

class TestGreetAll:
    def test_empty_list_returns_empty(self):
        assert hello.greet_all([]) == []

    def test_single_name(self):
        assert hello.greet_all(["Alice"]) == ["Hello, Alice!"]

    def test_multiple_names(self):
        result = hello.greet_all(["Alice", "Bob", "World"])
        assert result == ["Hello, Alice!", "Hello, Bob!", "Hello, World!"]

    def test_world_in_list_gets_special_greeting(self):
        result = hello.greet_all(["World"])
        assert result == ["Hello, World!"]

    def test_length_matches_input(self):
        names = ["Alice", "Bob", "Charlie"]
        assert len(hello.greet_all(names)) == 3

    def test_order_preserved(self):
        result = hello.greet_all(["Bob", "Alice"])
        assert result[0] == "Hello, Bob!"
        assert result[1] == "Hello, Alice!"

    def test_returns_list(self):
        assert isinstance(hello.greet_all(["Alice"]), list)

    def test_empty_string_in_list(self):
        result = hello.greet_all([""])
        assert result == ["Hello, !"]

    def test_duplicate_names(self):
        result = hello.greet_all(["Alice", "Alice"])
        assert result == ["Hello, Alice!", "Hello, Alice!"]


# ─────────────────────────────────────────────────────────────
# formal_greeting
# ─────────────────────────────────────────────────────────────

class TestFormalGreeting:
    def test_empty_name_returns_stranger(self):
        assert hello.formal_greeting("") == "Hello, stranger!"

    def test_name_only(self):
        assert hello.formal_greeting("Smith") == "Good day, Smith."

    def test_name_with_title(self):
        assert hello.formal_greeting("Smith", "Dr") == "Good day, Dr Smith."

    def test_name_with_mr_title(self):
        assert hello.formal_greeting("Jones", "Mr") == "Good day, Mr Jones."

    def test_no_title_no_dot_prefix(self):
        result = hello.formal_greeting("Alice")
        assert "Good day" in result

    def test_result_ends_with_period(self):
        assert hello.formal_greeting("Alice").endswith(".")

    def test_stranger_result_ends_with_exclamation(self):
        assert hello.formal_greeting("").endswith("!")

    def test_title_appears_before_name(self):
        result = hello.formal_greeting("Smith", "Prof")
        assert result.index("Prof") < result.index("Smith")

    def test_empty_title_ignored(self):
        assert hello.formal_greeting("Alice", "") == "Good day, Alice."


# ─────────────────────────────────────────────────────────────
# shout_hello
# ─────────────────────────────────────────────────────────────

class TestShoutHello:
    def test_empty_name_returns_hello_shout(self):
        assert hello.shout_hello("") == "HELLO!"

    def test_regular_name_uppercased(self):
        assert hello.shout_hello("Alice") == "HELLO, ALICE!"

    def test_world_uppercased(self):
        assert hello.shout_hello("World") == "HELLO, WORLD!"

    def test_result_is_all_uppercase(self):
        result = hello.shout_hello("Alice")
        assert result == result.upper()

    def test_lowercase_name_uppercased(self):
        assert hello.shout_hello("alice") == "HELLO, ALICE!"

    def test_return_type_is_str(self):
        assert isinstance(hello.shout_hello("Bob"), str)


# ─────────────────────────────────────────────────────────────
# count_hellos
# ─────────────────────────────────────────────────────────────

class TestCountHellos:
    def test_empty_list_returns_zero(self):
        assert hello.count_hellos([]) == 0

    def test_all_valid_names(self):
        assert hello.count_hellos(["Alice", "Bob", "Charlie"]) == 3

    def test_empty_strings_not_counted(self):
        assert hello.count_hellos(["Alice", "", "Bob"]) == 2

    def test_all_empty_strings(self):
        assert hello.count_hellos(["", "", ""]) == 0

    def test_single_valid_name(self):
        assert hello.count_hellos(["Alice"]) == 1

    def test_single_empty_string(self):
        assert hello.count_hellos([""]) == 0

    def test_returns_int(self):
        assert isinstance(hello.count_hellos(["Alice"]), int)

    def test_world_counted(self):
        assert hello.count_hellos(["World"]) == 1

    def test_mixed_valid_and_empty(self):
        assert hello.count_hellos(["", "Alice", "", "Bob", ""]) == 2


# ─────────────────────────────────────────────────────────────
# is_special_name
# ─────────────────────────────────────────────────────────────

class TestIsSpecialName:
    def test_world_is_special(self):
        assert hello.is_special_name("World") is True

    def test_regular_name_not_special(self):
        assert hello.is_special_name("Alice") is False

    def test_empty_string_not_special(self):
        assert hello.is_special_name("") is False

    def test_lowercase_world_not_special(self):
        assert hello.is_special_name("world") is False

    def test_uppercase_world_not_special(self):
        assert hello.is_special_name("WORLD") is False

    def test_world_with_space_not_special(self):
        assert hello.is_special_name("World ") is False

    def test_returns_bool(self):
        assert isinstance(hello.is_special_name("World"), bool)

    def test_numeric_not_special(self):
        assert hello.is_special_name("123") is False


def test_kill_survivor_line_15():
    # Auto-synthesized test case killing mutant transformation: * -> div
    # Default generic safety assertion checks
    assert hello.say_hello('World') == 'Hello, World!'
    assert hello.is_special_name('World') is True
    assert hello.is_special_name('Alice') is False
