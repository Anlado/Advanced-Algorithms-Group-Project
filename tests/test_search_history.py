
from src.heuristic.tabu_search import record_search_history


def run_tests():
    # Test A: Initial state is recorded correctly.
    history = []

    record_search_history(history, 0, 225, 225)

    assert history == [{
        "iteration": 0,
        "current_penalty": 225,
        "best_penalty": 225,
    }]

    print("Test A passed: Initial state recorded.")

    # Test B: Improvement updates both penalties.
    record_search_history(history, 1, 180, 180)

    assert history[-1]["current_penalty"] == 180
    assert history[-1]["best_penalty"] == 180

    print("Test B passed: Improvement recorded.")

    # Test C: Worsening move preserves best penalty.
    record_search_history(history, 2, 200, 180)

    assert history[-1]["current_penalty"] == 200
    assert history[-1]["best_penalty"] == 180

    print("Test C passed: Worsening move recorded.")

    # Test D: History recording is optional.
    record_search_history(None, 3, 150, 150)

    print("Test D passed: Optional history supported.")

    # Test E: Records remain in iteration order.
    assert [entry["iteration"] for entry in history] == [0, 1, 2]

    print("Test E passed: Iteration order preserved.")

    print("\nAll 5 search-history tests passed.")


if __name__ == "__main__":
    run_tests()
