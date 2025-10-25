# ⚠️ This program works only when you already have "project1devs/devs.csv" file.

from logic import *

def main():
    # ------------ get input --------------

    # Read csv file with name,dev columns
    devs_path = os.path.join("../../project1devs", "devs.csv")
    if not os.path.exists(devs_path):
        raise SystemExit(f'devs.csv not found at {devs_path}')
    
    DEVS = []
    try:
        with open(devs_path, 'r', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                DEVS.append(row)
    except FileNotFoundError:
        print('Unable to open the file.')

    # First element is header, skip
    DEVS = DEVS[1:]
    
    # ----------------- !!NEW!! pairing -------------------
    
    SIMILARITY = []
    accepted = [] 
    rejected = [] # could be useful for different method?

    
    for dev_a, dev_b in combinations(DEVS, 2):

        # Pre-process both developers
        feats_a = process(dev_a)
        feats_b = process(dev_b)
        name_a, first_a, last_a, i_first_a, i_last_a, email_a, prefix_a = feats_a
        name_b, first_b, last_b, i_first_b, i_last_b, email_b, prefix_b = feats_b
        
        # Conditions of Bird heuristic
        c1 = sim(name_a, name_b)
        c31 = sim(first_a, first_b)
        c32 = sim(last_a, last_b)
        c2 = sim(prefix_b, prefix_a)
        c4 = c5 = c6 = c7 = False

        # Since lastname and initials can be empty, perform appropriate checks
        if i_first_a != '' and last_a != '':
            c4 = i_first_a in prefix_b and last_a in prefix_b
        if i_last_a != '':
            c5 = i_last_a in prefix_b and first_a in prefix_b
        if i_first_b != '' and last_b != '':
            c6 = i_first_b in prefix_a and last_b in prefix_a
        if i_last_b != '':
            c7 = i_last_b in prefix_a and first_b in prefix_a
        
        # Get all email data and similarity socres
        e_score, same_dom, norm_a, norm_b, alpha_a, alpha_b, domain_a, domain_b = email_similarity_score(email_a, email_b)
        
        # Check if the pair has good Bird heuristic score 
        t = THRESHOLD - 0.1
        keep_by_score = (
            (c1  >= t       and e_score >= t) or
            (c32 >= t  and c31 >= t and e_score >= t) or
            (initials_match(first_a, last_a, first_b, last_b) and e_score >= t)
        )

        # Check if the pair is high-likely same person
        strong_match = safe_same_person(feats_a, feats_b)
        
        # create row only once (to avoid undefined variables)
        row = [
            dev_a[0], email_a, dev_b[0], email_b,
            c1, c2, c31, c32, c4, c5, c6, c7, e_score,
            int(strong_match), int(keep_by_score)
        ]

        # Add the pair with a high likelihood of TP to the accepted list
        if strong_match:
            accepted.append(row)
            continue

        # Add the pair with a high likelihood of FP to the rejected list
        if avoid_fp(feats_a, feats_b):
            rejected.append(row)
            continue

        # Add the pair with good Bird heuristic score to the accepted list
        if keep_by_score:
            accepted.append(row)
        else:
            rejected.append(row)

    # ------------ generate output --------------

    SIMILARITY = accepted

    # Generate CSV file
    cols = [
        "name_1","email_1","name_2","email_2",
        "c1_fullname","c2_prefix","c3_first","c3_last","c4","c5","c6","c7",
        "email_score","rule_strong_match","rule_keep_by_score"
    ]

    df = pd.DataFrame(SIMILARITY, columns=cols)

    out_dir = "../../project1devs"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"devs_similarity_improved_t={THRESHOLD}.csv")
    df.to_csv(out_path, index=False, header=True)

    # Show the number of threshold, committers, and generated pairs
    with open(devs_path, 'r', newline='') as f:
        num_devs = sum((1 for _ in f)) - 1
    
    with open(out_path, 'r', newline='') as f:
        num_pairs = sum((1 for _ in f)) - 1

    print(f'✅ Threshold: {THRESHOLD}')
    print(f'✅ Number of committers: {num_devs}')
    print(f'✅ Number of pairs: {num_pairs}')
    print(f'✅ Output file: {out_path}')

if __name__ == "__main__":
    main()