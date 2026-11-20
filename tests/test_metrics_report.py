
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.reporting.metrics_report import export_metrics


def run_tests():
    sections = {f"S{i}": None for i in range(8)}
    rooms = {f"R{i}": None for i in range(4)}
    timeslots = {f"T{i}": None for i in range(6)}
    instructors = {f"I{i}": None for i in range(4)}

    with TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "out" / "metrics.json"

        # Test A: Export creates the JSON file.
        result = export_metrics(
            sections,
            rooms,
            timeslots,
            instructors,
            225,
            0,
            True,
            0.03,
            0.01,
            output_path,
            hard_constraint_violations=0,
        )

        assert output_path.exists()
        assert result == output_path
        print("Test A passed: Metrics file created.")

        with output_path.open(encoding="utf-8") as file:
            metrics = json.load(file)

        # Test B: Dataset sizes are recorded correctly.
        assert metrics["dataset"] == {
            "sections": 8,
            "rooms": 4,
            "timeslots": 6,
            "instructors": 4,
        }
        print("Test B passed: Dataset sizes recorded.")

        # Test C: Penalty improvement is calculated correctly.
        optimization = metrics["optimization"]

        assert optimization["initial_penalty"] == 225
        assert optimization["final_penalty"] == 0
        assert optimization["penalty_reduction"] == 225
        assert optimization["improvement_percent"] == 100.0
        print("Test C passed: Penalty improvement calculated.")

        # Test D: Feasibility is recorded correctly.
        assert metrics["feasibility"]["feasible"] is True
        assert metrics["feasibility"]["hard_constraint_violations"] == 0
        print("Test D passed: Feasibility recorded.")

        # Test E: Runtime measurements are correct.
        runtime = metrics["runtime_seconds"]

        assert runtime["construction"] == 0.03
        assert runtime["optimization"] == 0.01
        assert runtime["total"] == 0.04
        print("Test E passed: Runtime measurements recorded.")

        # Test F: Zero initial penalty avoids division by zero.
        export_metrics(
            sections, rooms, timeslots, instructors,
            0, 0, True, 0.02, 0.01, output_path,
        )

        with output_path.open(encoding="utf-8") as file:
            metrics = json.load(file)

        assert metrics["optimization"]["improvement_percent"] == 0.0
        assert metrics["optimization"]["penalty_reduction"] == 0
        print("Test F passed: Zero initial penalty handled.")

        # Test G: Worsening solutions produce negative improvement.
        export_metrics(
            sections, rooms, timeslots, instructors,
            100, 125, False, 0.02, 0.01, output_path,
            hard_constraint_violations=2,
        )

        with output_path.open(encoding="utf-8") as file:
            metrics = json.load(file)

        assert metrics["optimization"]["penalty_reduction"] == -25
        assert metrics["optimization"]["improvement_percent"] == -25.0
        assert metrics["feasibility"]["hard_constraint_violations"] == 2
        print("Test G passed: Worsening solution handled.")

    print("\nAll 7 metrics-report tests passed.")


if __name__ == "__main__":
    run_tests()
