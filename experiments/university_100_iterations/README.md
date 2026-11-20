# University Timetabling — 100-Iteration Experiment

## Dataset

- 525 course sections
- 100 rooms
- 60 timeslots
- 180 instructors
- 105 student cohorts representing 10,500 students

Dataset: `data/university/`

## Configuration

- Random seed: 42
- Maximum Tabu Search iterations: 100
- Tabu tenure: 10
- Idle weight: 1
- Preference weight: 45
- Maximum consecutive non-improving iterations: 30

## Results

| Metric | Value |
|---|---:|
| Initial penalty | 50,055 |
| Final penalty | 20,565 |
| Penalty reduction | 29,490 |
| Improvement | 58.92% |
| Construction runtime | 142.28 seconds |
| Optimization runtime | 9.71 seconds |
| Total runtime | 151.99 seconds |
| Scheduled sections | 525 / 525 |
| Hard-constraint violations | 0 |

## Observations

Tabu Search consistently reduced the soft-constraint penalty throughout the 100 recorded iterations.

The optimization curve shows diminishing improvement per iteration, but no clear plateau by iteration 100.

The resulting timetable satisfies all implemented hard constraints.

## Artifacts

- `metrics.json`: Evaluation metrics and runtime
- `feasibility_report.md`: Hard-constraint verification
- `quality_curve.png`: Penalty progression over 100 iterations

## Reproduction

Run the project with the university dataset and the configuration listed above:

```bash
python -u run_modular_project.py
```

The results are deterministic only to the extent that all randomness is controlled by the configured seed.