## Selected project on GitHub: https://github.com/facebook/react

### Inspection
c4 (first_nameA in prefixB and last_nameA in prefixB)
c5 (last_nameA in prefixB and first_nameA in prefixB)
c6 (first_nameB in prefixA and last_nameB in prefixA)
c7 (last_nameB in prefixA and first_nameB in prefixA)

These conditions produce too many false positives because many last names consist of only a single letter.  
For example:  
Abishek Ilang (abishekilango@protonmail.com) and Anastasia A (sacret@nm.ru).  

Although their names and emails have little similarity, the last name “A” from the second committer is included in the prefix of the first committer’s email, leading to an incorrect match.

Therefore, only (c1_check), (c2_check), and (c3_check) were used for data extraction.
After applying the modified conditions with a 0.8 threshold, 963 rows were returned.

### Found cases

**Case 1:** Different names and emails, but a single-letter last name causes overlap
Example (introduced during inspection):
Abishek Ilang — abishekilango@protonmail.com
Anastasia A — sacret@nm.ru
→ Even though the names and emails are unrelated, the single-letter last name “A” appears in the other committer’s email prefix, resulting in a false positive.


**Case 2:** *Different names but similar email prefixes*  
Example:  
Aaron Brager — getaaron@gmail.com  
Dan Abramov — gaearon@fb.com  
→ Even though the names are completely different, the email prefixes ("getaaron" and "gaearon") are similar enough to produce a false positive.

**Case 3:** *Prefix reused as part of the domain name*  
Example:  
Kurt Ruppel — me@kurtruppel.com  
Rafael Angeline — me@rafaelangeline.com  
→ Here, the prefix "me" is identical for both users, but it’s actually a generic username used in combination with personalized domains. This leads to another type of false positive.

**Forwarding**
1. Add length and similarity thresholds
- Only consider a substring match valid if the name segment is at least n characters long (e.g., >2 characters).
- Combine substring checks with a similarity threshold (e.g., sim(prefix_a, prefix_b) > 0.7) to filter out weak matches.
2. Exclude single-letter name components
- Before evaluation, filter out cases where len(first) or len(last) == 1, since these tend to cause false positives.
3. Refine prefix matching logic
- Instead of in checks (first_a in prefix_b), use a normalized similarity function:
EX) c4 = sim(prefix_b, f"{i_first_a}{last_a}") > 0.8
This might reduce the impact of incidental substring overlap.
4. Leverage full-name similarity more heavily
- Prioritize c1, c2, and c3 (direct similarity scores) as the main matching criteria.
- Use c4–c7 only as secondary checks when similarity scores are borderline.
5. Implement a combined score
- Compute a weighted sum of similarities 
EX) score = 0.4*c1 + 0.3*c2 + 0.2*c31 + 0.1*c32
    if score > 0.7: match = True
This helps balance different indicators and reduce noise from substring-based rules.
