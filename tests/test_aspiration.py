
from src.heuristic.tabu_search import meets_aspiration_criterion


# ============================================================
# ASPIRATION CRITERION TESTS
# ============================================================


# Test A: A candidate better than the best-known solution
# satisfies aspiration.
assert meets_aspiration_criterion(100, 120)

print("Test A passed: Better candidate satisfies aspiration.")


# Test B: A candidate equal to the best-known solution
# does not satisfy aspiration.
assert not meets_aspiration_criterion(120, 120)

print("Test B passed: Equal candidate does not satisfy aspiration.")


# Test C: A candidate worse than the best-known solution
# does not satisfy aspiration.
assert not meets_aspiration_criterion(150, 120)

print("Test C passed: Worse candidate does not satisfy aspiration.")


# Test D: A candidate with zero penalty satisfies aspiration
# when the best-known penalty is positive.
assert meets_aspiration_criterion(0, 45)

print("Test D passed: Zero-penalty improvement satisfies aspiration.")


# Test E: A candidate cannot improve on an already
# optimal zero-penalty solution when penalties are nonnegative.
assert not meets_aspiration_criterion(0, 0)

print("Test E passed: Zero-penalty tie does not satisfy aspiration.")


print("\nAll 5 aspiration criterion tests passed.")
