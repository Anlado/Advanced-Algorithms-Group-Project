
import json
from pathlib import Path


# Export dataset information, optimization results, feasibility,
# and runtime measurements to a machine-readable JSON file.
# Return the path of the generated metrics file.
def export_metrics(
    sections,
    rooms,
    timeslots,
    instructors,
    initial_penalty,
    final_penalty,
    is_feasible,
    construction_runtime,
    optimization_runtime,
    output_path,
    hard_constraint_violations=None,
):
    output_path = Path(output_path)

    # Calculate the improvement achieved by Tabu Search.
    penalty_reduction = initial_penalty - final_penalty

    # Avoid division by zero when the initial solution
    # already has a penalty of zero.
    if initial_penalty > 0:
        improvement_percent = (
            penalty_reduction / initial_penalty
        ) * 100
    else:
        improvement_percent = 0.0

    total_runtime = construction_runtime + optimization_runtime

    # Keep the exported results grouped by their purpose.
    metrics = {
        "dataset": {
            "sections": len(sections),
            "rooms": len(rooms),
            "timeslots": len(timeslots),
            "instructors": len(instructors),
        },
        "optimization": {
            "initial_penalty": initial_penalty,
            "final_penalty": final_penalty,
            "penalty_reduction": penalty_reduction,
            "improvement_percent": round(improvement_percent, 2),
        },
        "feasibility": {
            "feasible": is_feasible,
            "hard_constraint_violations": hard_constraint_violations,
        },
        "runtime_seconds": {
            "construction": round(construction_runtime, 6),
            "optimization": round(optimization_runtime, 6),
            "total": round(total_runtime, 6),
        },
    }

    # Create the output directory and write formatted JSON.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4, allow_nan=False)
        file.write("\n")

    return output_path
