# Project Work Pipeline: University Course Timetabling CLI

## Goal

By Saturday, November 14, deliver a reproducible command-line program that reads the provided Purdue University timetabling dataset, uses Tabu Search to remove hard-constraint violations and then reduce the soft-constraint penalty, and reports the results.

Use the Purdue dataset as a benchmark. Do not describe it as Kennesaw State University data. Implement and report only constraints that can be evaluated from the available dataset; list unsupported requirements as limitations.

## Work plan

### Tuesday, November 10 — Agree on scope and divide work

- Inspect the XML structure and identify the fields available for classes, rooms, students, and constraints.
- Agree which hard constraints the dataset supports and which soft constraints will be scored.
- Decide on the schedule representation, the hard and soft scores, the Tabu Search neighborhood, and the output format.
- Divide ownership across data parsing, validation, Tabu Search, and CLI/documentation. Combine roles as needed.

**Checkpoint:** The team has a written scope, a map of relevant data fields, and clear ownership.

### Wednesday, November 11 — Data loading, validation, and CLI foundation

- Implement an XML parser for the agreed fields.
- Add a CLI skeleton and an `inspect` command that summarizes the input dataset.
- Implement hard-constraint validation and soft-penalty scoring independently of the search algorithm.
- Add small tests for valid assignments and known violations.

**Checkpoint:** The CLI can load the Purdue XML, show a useful summary, and validate a schedule with clear violation messages.

### Thursday, November 12 — Tabu Search, phase 1: hard constraints

- Build an initial schedule by giving each class an allowed time and room, chosen with the fixed random seed. This schedule does not need to be feasible.
- Implement Tabu Search that minimizes the number of hard-constraint violations.
- Use a well-defined neighborhood, such as moving a conflicting class to a different allowed time or room.
- Add a tabu list (for example, forbid moving a class back to a time/room it just left for a set number of iterations), an aspiration rule (allow a tabu move if it gives a new best), best-solution tracking, and a stopping limit.
- Make score updates incremental (re-score only the classes affected by a move) so iterations stay fast on 896 classes.

**Checkpoint:** One repeatable run reports the hard-violation count of the initial schedule and of the best schedule found. If zero violations is not reached, report the remaining violations rather than marking the schedule feasible.

### Friday, November 13 — Tabu Search, phase 2: soft constraints

- Continue from the best phase-1 schedule and minimize the soft penalty (time/room preferences, soft group constraints, student conflicts and gaps).
- Reject or heavily penalize any move that introduces a hard violation, so feasibility is kept.
- Record the best score at each iteration for the quality curve.
- Tune the key parameters (tabu tenure, iteration or time limit) and store them in the configuration file.

**Checkpoint:** The CLI runs the full Tabu Search and reports the initial, end-of-phase-1, and final scores using the same validator and score.

### Saturday, November 14 — End-to-end verification and delivery

- Run the project from a clean checkout using the documented command.
- Generate the schedule, feasibility report, metrics, and quality plot.
- Run final tests and a few scaling runs if time permits; report measured results and limitations.
- Finish the README and methods note, then package the deliverable.

**Checkpoint:** A documented one-command run recreates the outputs, and the final package contains the code, configuration, results, and documentation.

## Suggested CLI

```text
python -m uctp inspect --input pu-fal07-llr.xml
python -m uctp validate --input pu-fal07-llr.xml --schedule out/schedule.csv
python -m uctp solve --input pu-fal07-llr.xml --seed 42 --output-dir out
```

Keep CLI argument handling separate from XML parsing, constraint validation, and search logic so those parts can be tested independently.

## Suggested deliverables

- A concise README with setup, commands, expected runtime/output paths, team roles, and limitations.
- Organized source for the CLI, data loading, model/validation, and Tabu Search.
- A configuration containing parameters and the fixed random seed.
- Generated outputs such as `schedule.csv`, `feasibility_report.md`, `metrics.json`, and a quality curve plot.
- A short methods note describing the model, constraints, Tabu Search (representation, neighborhood, tabu list, parameters), and measured results.
- A ZIP archive containing the final deliverable.

## Scope guardrails

- Prioritize course scheduling, room/time assignments, and instructor/student conflicts only where the dataset provides the necessary information.
- Keep optional extensions out of scope until the core workflow works.
- Clearly distinguish hard constraints checked by the program from constraints that are unsupported by the input data.
- Measure improvement by comparing the initial schedule with the Tabu Search result using the same input, validator, and score.
- Fix the random seed for reproducibility and report actual measurements rather than claiming optimality.
