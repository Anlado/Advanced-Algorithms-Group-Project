
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def export_quality_curve(search_history, output_path):
    """
    Export a plot of current and best-known penalties by iteration.

    Expected history format:
    [
        {
            "iteration": 0,
            "current_penalty": 225,
            "best_penalty": 225,
        },
        ...
    ]
    """
    if not search_history:
        raise ValueError("Search history cannot be empty.")

    iterations = [entry["iteration"] for entry in search_history]
    current_penalties = [
        entry["current_penalty"] for entry in search_history
    ]
    best_penalties = [
        entry["best_penalty"] for entry in search_history
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        iterations,
        current_penalties,
        label="Current Penalty",
        marker="o",
        linewidth=1.5,
        alpha=0.7,
    )

    ax.plot(
        iterations,
        best_penalties,
        label="Best-Known Penalty",
        marker="s",
        linewidth=2,
    )

    ax.set_title("Tabu Search Optimization Quality Curve")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Soft-Constraint Penalty")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path
