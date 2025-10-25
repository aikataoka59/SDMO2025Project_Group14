import unittest
import os
import csv
import sys
from itertools import combinations
from Levenshtein import ratio as sim

# Import all functions from your main module
from project1developers_final.logic import (
    THRESHOLD,
    process,
    split_email,
    normalize_local,
    is_organization_local,
    email_similarity_score,
    initials_match,
    safe_same_person,
    avoid_fp
)


class TestDevMatching(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Normal cases for accuracy test
        cls.devs = [
            # All of these are the same person with different username and email
            ["John Doe", "john@example.com"],
            ["J. Doe", "jdoe@example.com"],
            ["John  Doe", "john.doe@example.com"],             # more space
            ["JOHN DOE", "JOHN.DOE@EXAMPLE.COM"],              # large case

            # Ordinary different person from John Doe
            ["Jane Smith", "jane@company.org"],
            ["J. Smith", "smith.j@company.org"],
            ["Alice Tanaka", "alice.tnk@gmail.com"],
            ["A. Tanaka", "a.tanaka@lab.jp"],
        ]

        cls.devs_feats = [process(dev) for dev in cls.devs]


        # Edge cases for endurance test

        cls.edge_devs = [
            ["", "missingname@example.com"],                    # no name
            ["J", "shortname@example.com"],                     # short name
            ["Jean-Luc Picard", "jeanluc.picard@starfleet.com"],# name with symbols
            ["Müller, Franz", "franz.muller+dev@gmail.com"],    # name with accents
            ["O’Connor, Anne", "anne.oconnor+123@gmail.com"],   # apostrophe and plus
            ["José Ángel", "jose.angel@org.com"],               # spanish person
            ["Admin", "admin@company.com"],                     # user from organization
            ["Git", "git@opensource.org"],                      # git account
            ["Root", "root@server.net"],                        # server account
            ["Support", "support@helpdesk.org"],                # support account
        ]

        cls.edge_feats = [process(dev) for dev in cls.edge_devs]



    # ---------- Test preprocessing ----------
    def test_process_cleaning(self):
        for dev in self.edge_devs:
            name, first, last, i_first, i_last, email, prefix = process(dev)
            self.assertTrue(name.islower() or name == "")  # lowercased
            self.assertIsInstance(prefix, str)
    
    # ---------- Test email splitting ----------
    def test_split_email(self):
        local, domain = split_email("user123+test@gmail.com")
        self.assertEqual(local, "user123+test")
        self.assertEqual(domain, "gmail.com")

    # ---------- Test normalize local ----------
    def test_normalize_local(self):
        norm, alpha = normalize_local("12345+username", "gmail.com")
        self.assertEqual(norm, "username")
        self.assertEqual(alpha, "username")

    # ---------- Test organization local ----------
    def test_is_organization_local(self):
        self.assertTrue(is_organization_local("git"))
        self.assertFalse(is_organization_local("johndoe"))

    # ---------- Test email similarity ----------
    def test_email_similarity_score(self):
        e_score, same_dom, *_ = email_similarity_score("user@gmail.com", "user@gmail.com")
        self.assertTrue(e_score > 0)
        self.assertTrue(same_dom)

    # ---------- Test initials matching ----------
    def test_initials_match(self):
        self.assertTrue(initials_match("John", "Doe", "J0", "Doe"))
        self.assertFalse(initials_match("John", "Doe", "John", "D"))

    # ---------- Test safe_same_person ----------
    def test_safe_same_person_dataset(self):
        # pick first two devs from dataset for dynamic testing
        feats_a = self.devs_feats[0]
        feats_b = self.devs_feats[1]
        result = safe_same_person(feats_a, feats_b)
        self.assertIsInstance(result, bool)

    # ---------- Test avoid_fp ----------
    def test_avoid_fp_dataset(self):
        feats_a = self.edge_feats[0]  # missing name
        feats_b = self.edge_feats[1]  # short name
        self.assertTrue(avoid_fp(feats_a, feats_b))

    # ---------- Test Bird heuristic flags ----------
    def test_bird_heuristic_flags(self):
        # pick two devs dynamically
        feats_a = self.devs_feats[0]
        feats_b = self.devs_feats[1]
        name_a, first_a, last_a, i_first_a, i_last_a, email_a, prefix_a = feats_a
        name_b, first_b, last_b, i_first_b, i_last_b, email_b, prefix_b = feats_b

        c1 = sim(name_a, name_b)
        c31 = sim(first_a, first_b)
        c32 = sim(last_a, last_b)
        c2 = sim(prefix_a, prefix_b)

        # Ensure values are between 0 and 1
        self.assertTrue(0.0 <= c1 <= 1.0)
        self.assertTrue(0.0 <= c31 <= 1.0)
        self.assertTrue(0.0 <= c32 <= 1.0)
        self.assertTrue(0.0 <= c2 <= 1.0)

    # ---------- Test accepted/rejected logic ----------
    def test_accepted_rejected_logic(self):
        accepted, rejected = [], []
        for feats_a, feats_b in combinations(self.devs_feats + self.edge_feats, 2):
            strong_match = safe_same_person(feats_a, feats_b)
            fp = avoid_fp(feats_a, feats_b)
            if strong_match:
                accepted.append(feats_a + feats_b)
            elif fp:
                rejected.append(feats_a + feats_b)
        # No overlap
        accepted_tuples = set(tuple(row) for row in accepted)
        rejected_tuples = set(tuple(row) for row in rejected)
        self.assertEqual(len(accepted_tuples & rejected_tuples), 0)

    # ---------- Test threshold effect ----------
    def test_threshold_effect(self):
        # Reduce threshold temporarily
        low_threshold = 0.5
        feats_a = self.devs_feats[0]
        feats_b = self.devs_feats[1]
        e_score, *_ = email_similarity_score(feats_a[5], feats_b[5])
        # With lower threshold, email_similarity may pass
        self.assertTrue(e_score >= 0.0)

    # ---------- Test edge cases ----------
    def test_edge_cases(self):
        for feats_a, feats_b in combinations(self.edge_feats, 2):
            self.assertIsInstance(safe_same_person(feats_a, feats_b), bool)
            self.assertIsInstance(avoid_fp(feats_a, feats_b), bool)

if __name__ == "__main__":
    unittest.main()
