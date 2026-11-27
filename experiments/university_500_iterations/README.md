
# University Timetabling — 500-Iteration Experiment

## Dataset
- Students represented: 10,500
- Course sections: 525
- Rooms: 100
- Instructors: 180
- Timeslots: 60

## Tabu Search Configuration
- Random seed: 42
- Maximum iterations: 500
- Tabu tenure: 10
- Maximum consecutive iterations without improvement: 30
- Idle penalty weight: 1
- Preference penalty weight: 45

## Results
- Initial soft-constraint penalty: 50,055
- Final soft-constraint penalty: 855
- Penalty reduction: 49,200
- Improvement: 98.29%
- Construction runtime: 141.24 seconds
- Optimization runtime: 48.10 seconds
- Total runtime: 189.34 seconds

## Feasibility
- Scheduled sections: 525/525
- Hard-constraint violations: 0
- Status: PASS

## Interpretation
The 500-iteration experiment achieved a 98.29% reduction in the weighted soft-constraint penalty while preserving timetable feasibility.

The quality curve shows continued improvement through iteration 500, with diminishing returns toward the end. The result does not establish global optimality.

## Reproduction
Run from the project root:

1. Set `tabu_search.max_iterations` to 500 in `config.json`.
2. Keep the remaining configuration values listed above.
3. Run `python -u run_project.py`.

Generated outputs are written to `out/`.
