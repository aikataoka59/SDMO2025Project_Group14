
import csv
import pandas as pd
import unicodedata
import string
import os
import re
from itertools import combinations
from Levenshtein import ratio as sim

# ------------ config --------------

# Change threshold value to make the rules strict or soft and change the amount of generated similar pairs.  
THRESHOLD = 0.59      # closer to 1 -> more strict

MIN_NAME_LEN  = 3       # A name with less than this num of letter -> Short name

DOM_WEIGHT = 0.10       # How domain part of the email will be prioritised (e.g. @gmail.com)
LOC_WEIGHT = 0.90       # How local part of the email will be prioritised (e.g. username123@)
ORG_DOM_WEIGHT = 0.80       # How domain part of the email will be prioritised when it has organaizational local
ORG_LOC_WEIGHT = 0.20       # How local part of the email will be prioritised when it has organaizational local

# A list of frequently occurring organisational email locals
COMMON_ORGANIZATION_LOCALS = {"git", "admin", "root", "support", "info", "noreply", "webmaster", "ci", "build", "bot", "github", "mail","git", "dev", "me", "contact", "hello"}

# ------------ preprocessing  -------------- 
# Function for pre-processing each name,email
def process(dev):
    name: str = dev[0]

    # Remove punctuation
    trans = name.maketrans("", "", string.punctuation)
    name = name.translate(trans)
    # Remove accents, diacritics
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    # Lowercase
    name = name.casefold()
    # Strip whitespace
    name = " ".join(name.split())

    # Attempt to split name into firstname, lastname by space
    parts = name.split(" ")
    # Expected case
    if len(parts) == 2:
        first, last = parts
    # If there is no space, firstname is full name, lastname empty
    elif len(parts) == 1:
        first, last = name, ""
    # If there is more than 1 space, firstname is until first space, rest is lastname
    else:
        first, last = parts[0], " ".join(parts[1:])

    # Take initials of firstname and lastname if they are long enough
    i_first = first[0] if len(first) > 1 else ""
    i_last = last[0] if len(last) > 1 else ""

    # Determine email prefix
    email: str = dev[1]
    prefix = email.split("@")[0].lower() # !!NEW!!: added .lower()

    return name, first, last, i_first, i_last, email, prefix


# ------------ !!NEW!! Chacking e-mail similarity --------------

def split_email(email: str):
    # Split email into local and domain
    email = email.strip().lower()
    if "@" in email:
        local, domain = email.split("@", 1)
    else:
        local, domain = email, ""
    return local, domain

def normalize_local(local: str, domain: str): 
    # Check if local has auto-generated numbers (ususally more than 5 nums) e.g. 12345+username@
    # If so, remove numbers and symbols and return it as normalized local
    # If not, retern the original as normalized local
    # Reterns normalized local and local with only alphabets

    if re.match(r"^\d{5,}\+", local):
        norm = re.sub(r"^\d+\+", "", local)
    else:
        norm = local
    alpha_only = re.sub(r"[^a-z]", "", norm)

    return norm, alpha_only

def is_organization_local(local: str):
    # Check whether it is organizational common local or not
    # e.g. mail@, dev@, github@, etc.
    # If so, the domain's priority will increase
    if local in COMMON_ORGANIZATION_LOCALS:
        return True
    return False

def email_similarity_score(email_a: str, email_b: str):
    # Get emial similarity socre and splited email addresses
    
    # Get local and domain from both emails
    local_a, domain_a = split_email(email_a)
    local_b, domain_b = split_email(email_b)

    # Get normalized and alpha-only locals for both emails
    norm_a, alpha_a = normalize_local(local_a, domain_a)
    norm_b, alpha_b = normalize_local(local_b, domain_b)

    # Get local and domain similarity score
    dom_sim = 1.0 if domain_a == domain_b else 0.0
    local_sim = max(sim(norm_a, norm_b), sim(alpha_a, alpha_b))

    # Check if both has organization local and change priority basesd on result
    org_local = is_organization_local(local_a) and is_organization_local(local_b)
    dom_w = ORG_DOM_WEIGHT if org_local else DOM_WEIGHT
    loc_w = ORG_LOC_WEIGHT if org_local else LOC_WEIGHT

    # Get email similarity score
    email_score = dom_w * dom_sim + loc_w * local_sim

    return email_score, (domain_a == domain_b), norm_a, norm_b, alpha_a, alpha_b, domain_a, domain_b

# ------------ !!NEW!! improved rules for pairing --------------

def is_short_name(part: str):
    # Check whether the name is short name
    # Returns boolean value
    return 0 < len(part) < MIN_NAME_LEN

def initials_match(first_a, last_a, first_b, last_b):
    # Check whether it has full name and pairs has same last name, and same initials of first name
    if last_a and last_b and last_a == last_b:
        if first_a and first_b and first_a[0] == first_b[0]:
            return True
    return False

def safe_same_person(feats_a, feats_b):
    # Check if the pair is high-likely same person and return boolean value
    # If so, the pairs will be added to the list when pairing

    # Get data of the pair
    name_a, first_a, last_a, i_first_a, i_last_a, email_a, prefix_a = feats_a
    name_b, first_b, last_b, i_first_b, i_last_b, email_b, prefix_b = feats_b

    # 1) exact same email -> return True
    if email_a.strip().lower() == email_b.strip().lower():
        return True

    # 2) exact same full name -> return True
    if name_a == name_b and name_a != "":
        return True

    # 3) same initials + strong email similarity -> return True
    e_score, *_ = email_similarity_score(email_a, email_b)
    if initials_match(first_a, last_a, first_b, last_b) and e_score >= THRESHOLD:
        return True
                
    # 4) strong full name + strong email similarity -> return True
    last_sim = sim(last_a, last_b)
    first_sim = sim(first_a, first_b)
    if last_sim >= THRESHOLD and first_sim >= THRESHOLD and e_score >= THRESHOLD:
        return True

    return False

def avoid_fp(feats_a, feats_b):
    # Check if the pair appears to be False Positive
    # If so, the pairs will be eliminated when pairing

    # Get data of the pair
    name_a, first_a, last_a, i_first_a, i_last_a, email_a, prefix_a = feats_a
    name_b, first_b, last_b, i_first_b, i_last_b, email_b, prefix_b = feats_b

    # Get all email data and similarity socres
    e_score, same_dom, norm_a, norm_b, alpha_a, alpha_b, domain_a, domain_b = email_similarity_score(email_a, email_b)

    # Check if any of names are missing
    missing_name_a = (first_a == "" or last_a == "")
    missing_name_b = (first_b == "" or last_b == "")

    # 1) missing name(s) + weak email -> exclude
    if (missing_name_a or missing_name_b) and e_score < THRESHOLD:
        return True
    if (missing_name_a and missing_name_b) and e_score < THRESHOLD:
        return True

    # 2) short names + weak email similarity -> exclude
    if (is_short_name(first_a) or is_short_name(last_a) or is_short_name(first_b) or is_short_name(last_b)):
        if e_score < THRESHOLD:
            return True

    # 3) organization like locals  + different domain -> exclude
    if is_organization_local(norm_a) or is_organization_local(norm_b):
        if domain_a != domain_b:
            return True
    
    # 4) weak email + similar name but different lastname -> exclude
    if last_a and last_b and last_a != last_b:
        if sim(first_a, first_b) >= 0.90 and e_score < 0.80:
            return True

    return False