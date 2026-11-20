# University Course Timetabling Using Tabu Search

**CS 6045 — Advanced Algorithms | Kennesaw State University | Fall 2026**

## Overview

This project addresses the **University Course Timetabling Problem (UCTP)**: assigning course sections to available timeslots and rooms while satisfying scheduling constraints and minimizing undesirable scheduling outcomes.

University timetabling is a combinatorial optimization problem. As the number of sections, instructors, rooms, and scheduling requirements increases, finding a feasible and high-quality timetable becomes increasingly challenging.

Our implementation uses a two-stage approach:

1. **Initial timetable construction:** Generate a complete timetable that satisfies the implemented hard constraints using constraint-satisfaction techniques.
2. **Tabu Search optimization:** Improve the initial timetable by minimizing weighted soft-constraint penalties while preserving feasibility.

The project is implemented in Python and evaluated using a synthetic university dataset.

## Algorithm Design

### Stage 1: Initial Feasible Timetable Construction

The initial timetable is generated using a constraint-based search strategy incorporating:

- **Minimum Remaining Values (MRV):** Prioritize sections with fewer feasible assignments.
- **Degree heuristic:** Help break ties by considering scheduling conflicts.
- **Least Constraining Value (LCV):** Prefer assignments that preserve scheduling flexibility.
- **Backtracking:** Reconsider earlier assignments when necessary to find a feasible solution.

The goal of this stage is to schedule all sections without violating hard constraints.

### Stage 2: Tabu Search Optimization

Once a feasible timetable has been constructed, Tabu Search improves its quality through local search.

The implementation includes:

- Single-section reassignment moves
- Two-section assignment swaps
- Hard-constraint validation of candidate moves
- Tabu memory to discourage recently reversed assignments
- An aspiration criterion that can override tabu restrictions
- Best-known solution tracking
- Bounded neighborhood sampling
- Incremental soft-constraint penalty evaluation
- Iteration and stagnation stopping criteria

The algorithm selects the best admissible sampled neighbor, including potentially worsening moves, while preserving the best solution found.

## Scheduling Constraints

### Hard Constraints

Hard constraints must be satisfied for a timetable to be considered feasible.

The implementation checks:

- Room capacity
- Laboratory requirements
- Instructor availability and required no-teach slots
- Instructor qualifications
- Room scheduling conflicts
- Instructor scheduling conflicts
- Cohort scheduling conflicts
- Missing or invalid assignments

### Soft Constraints

Soft constraints represent scheduling preferences rather than mandatory requirements.

The current optimization objective considers:

- **Cohort idle time:** Minimize gaps between scheduled classes for student cohorts.
- **Instructor timeslot preferences:** Penalize assignments outside instructors' preferred timeslots.

The objective combines these penalties using configurable weights.

A lower penalty indicates a better timetable under the implemented objective function.

## Dataset

The project uses a synthetic university dataset with the following characteristics:

| Attribute | Value |
|---|---:|
| Students represented | 10,500 |
| Course sections | 525 |
| Instructors | 180 |
| Rooms | 100 |
| Timeslots | 60 |

The dataset files are located in `data/university/`.

The synthetic dataset enables evaluation at the required scale without relying on sensitive institutional scheduling records.

## Installation and Execution

### Requirements

- Python 3
- Dependencies listed in `requirements.txt`

### Setup

Clone the repository:

```bash
git clone https://github.com/Anlado/Advanced-Algorithms-Group-Project.git
cd Advanced-Algorithms-Group-Project
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run the Project

Review `config.json` to select the dataset, output directory, random seed, and Tabu Search parameters.

Then execute:

```bash
python -u run_modular_project.py
```

The program constructs an initial feasible timetable, performs Tabu Search optimization, validates the resulting timetable, and generates evaluation outputs.

## Configuration

The `config.json` file controls the experiment settings.

Important parameters include:

| Parameter | Purpose |
|---|---|
| `random_seed` | Controls seeded randomness |
| `max_iterations` | Maximum Tabu Search iterations |
| `tabu_tenure` | Duration of tabu restrictions |
| `no_improvement_max_iterations` | Stagnation stopping threshold |
| `idle_weight` | Weight assigned to cohort idle-time penalties |
| `preference_weight` | Weight assigned to instructor preference penalties |

The exact configuration used for each documented experiment is recorded in its corresponding experiment README.

## Experimental Results

Two experiments have been documented using the synthetic university dataset.

| Metric | 100-Iteration Experiment | 500-Iteration Experiment |
|---|---:|---:|
| Initial penalty | 50,055 | 50,055 |
| Final penalty | 20,565 | 855 |
| Penalty reduction | 58.92% | 98.29% |
| Construction runtime | 142.28 s | 141.24 s |
| Optimization runtime | 9.71 s | 48.10 s |
| Hard-constraint violations | 0 | 0 |
| Scheduled sections | 525/525 | 525/525 |

Both experiments produced complete, feasible timetables under the implemented hard constraints.

The 500-iteration experiment achieved a **98.29% reduction in weighted soft-constraint penalties** relative to the initial timetable.

These results demonstrate substantial improvement on the evaluated synthetic dataset. They do not establish global optimality or guarantee equivalent performance on other datasets.

### Experiment Documentation

- [100-Iteration Benchmark](experiments/university_100_iterations/README.md)
- [500-Iteration Benchmark](experiments/university_500_iterations/README.md)

Each experiment directory includes evaluation metrics, a feasibility report, and a quality curve.

## Generated Outputs

After execution, the program writes its outputs to the configured output directory, normally `out/`.

| File | Description |
|---|---|
| `out/schedule.csv` | Optimized course timetable |
| `out/metrics.json` | Dataset, optimization, feasibility, and runtime metrics |
| `out/feasibility_report.md` | Hard-constraint validation results |
| `out/plots/quality_curve.png` | Current and best-known penalties across iterations |

Generated outputs are not intended to replace the preserved experimental benchmarks.

## Limitations and Future Work

Potential areas for further evaluation and improvement include:

- Testing across multiple random seeds
- Comparing different tabu tenures and neighborhood sampling budgets
- Measuring improving, neutral, and worsening moves
- Evaluating performance on additional datasets
- Investigating scalability beyond the current dataset
- Comparing Tabu Search with alternative optimization approaches

## Project Team

**CS 6045 — Advanced Algorithms, Fall 2026**

- Teriyana Mack — Data Modeling and Constraint Implementation
- Mithil Honkanadavar — Algorithm Design and Project Integration
- Brooke Ebetino — Related Work and Algorithm Evaluation
- Christian Tsoungui Nkoulou — Algorithm Implementation and Testing

## Academic Context

This repository contains a group project developed for CS 6045 Advanced Algorithms at Kennesaw State University.

The implementation and experiments are intended to investigate constraint-based timetable construction and Tabu Search as an approach to university course scheduling.
