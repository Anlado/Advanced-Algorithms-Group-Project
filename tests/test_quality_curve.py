
from pathlib import Path
from tempfile import TemporaryDirectory

from src.reporting.quality_curve import export_quality_curve


def run_tests():
    history = [
        {"iteration": 0, "current_penalty": 225, "best_penalty": 225},
        {"iteration": 1, "current_penalty": 180, "best_penalty": 180},
        {"iteration": 2, "current_penalty": 200, "best_penalty": 180},
        {"iteration": 3, "current_penalty": 90, "best_penalty": 90},
        {"iteration": 4, "current_penalty": 0, "best_penalty": 0},
    ]

    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "plots" / "quality_curve.png"

        result = export_quality_curve(history, output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        with output_path.open("rb") as file:
            assert file.read(8) == b"\x89PNG\r\n\x1a\n"

        print("Test A passed: Quality curve PNG created.")
        print("Test B passed: Output directory created.")
        print("Test C passed: File has valid PNG signature.")

    try:
        export_quality_curve([], "unused.png")
    except ValueError:
        print("Test D passed: Empty history rejected.")
    else:
        raise AssertionError("Expected ValueError for empty history.")

    print("\nAll 4 quality-curve tests passed.")


if __name__ == "__main__":
    run_tests()
