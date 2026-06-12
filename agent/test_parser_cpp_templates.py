from services.parser import CppASTAdapter


def test_cpp_template_angles_are_not_treated_as_relational_operators():
    src = """
#include <vector>

bool f(int x) {
    std::vector<int> values;
    std::vector<std::vector<int>> nested;
    return x < 5;
}
""".strip()

    adapter = CppASTAdapter()
    muts = adapter.parse_mutations("agent/template_case.cpp", src)

    # Ensure real comparison is still detected.
    relational = [m for m in muts if m.get("operator_type") == "relational_operator_replacement"]
    assert any(m.get("original_code") == "<" and m.get("line_number") == 6 for m in relational)

    # Ensure template angle brackets are not reported as relational mutations.
    template_line_rel = [m for m in relational if m.get("line_number") in [4, 5]]
    assert template_line_rel == []
