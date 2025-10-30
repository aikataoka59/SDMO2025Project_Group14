## Homebrew
Repo used: https://github.com/angular/angular

### Analysis
Most of the pairs are false positives even with a threshold of 0.99.

This is likely caused by this line:

``` df = df[df[["c1_check", "c2_check", "c3_check", "c4", "c5", "c6", "c7"]].any(axis=1)] ``` 

It causes the script to include every row where at least one heuristic is true. Heuristics c4-c7 are too loose to use with the `any(axis=1)` acting as `OR` condition resulting in false positives when c1-3 are low.

### Improvements
- Prefilter results with c1 (name) & c2 (email) before applying weaker heuristics from c4-c7
- Combine stricter heuristics such as c1 and c2 using `AND` instead of `OR`
- Combine different metrics for a total score for similarity
- Normalise emails before comparisation
- Group results for easier manual verification
- Verify edge cases from llm?
    - Can't send personal data to cloud & token limits, can't run locally