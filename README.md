# SDMO 2025 Projects Group 14 Submission

This repository contains output data and improved scripts and testing codes.
The selected project: Project 1 Developer de-duplication

## Contents

- `outputs/`: All analyzed output for each GitHub project (total 5) are stored here.
- `project1devs/`: Directory for output to be generated (Empty)
  - `devs.csv`: List of developers mined from eShopOnContainersProject
  - `devs_similarity_improved_t=0.X.csv`: Improved similarity tests for each pair of developers with similarity threshold 0.X
- `src/project1developers_final/`: Directory for the final script. Our own method.
  - `main.py`: Main script of our method.
  - `logic.py`:  Logic script of our method.
- `project1developers_original.py`: Original script demonstrating mining developer information and Bird heuristic to determine duplicate developers
- `pytest.ini`: Setting paths for testings
- `requirements.txt`: List of used libraries with specified versions


## Running the scripts

The scripts were developed and tested on a Mac (UNIX) environment with Python 3.10.
There should be no compatibility issues with running the scripts on Windows.

The versions of imported libraries are provided in `requirements.txt`. Some python testing requirements were added for unit testing.

It is recommended to create a Python virtual environment and install the exact versions there.

It is required `project1devs/` to have `devs.csv` before running the improved scripts.
Run project1developers_original.py first to generate `devs.csv`. 

Run `main.py` and `devs_similarity_improved_t=0.X.csv` will be generated in `project1devs/`.

To run the tests, type `pytest -v` in the first directory (not inside any of the directories)
