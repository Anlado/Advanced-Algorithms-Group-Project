UCTP focused repair update (experimental)

1. Back up your existing run_project.py.
2. Copy this run_project.py into the folder C:\Users\teriy\OneDrive\UCTP_AAPROJECT
3. Keep the existing data folder in that same directory.
4. In PyCharm Terminal run:
   cd "C:\Users\teriy\OneDrive\UCTP_AAPROJECT"
   python run_project.py --iterations 5 --candidates 10 --seed 42
5. Share the JSON output and out/conflicts.csv.

The script tries a targeted hard-conflict repair pass before Tabu Search.
It is still a partial UniTime evaluator, not full feasibility certification.
