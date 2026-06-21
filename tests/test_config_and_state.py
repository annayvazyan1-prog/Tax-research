"""Offline tests — no network or API keys required.

These cover the deterministic seams: the model registry, the decorrelation
invariant, state reducers, and JSON parsing. The LLM-driven nodes need live
keys and are exercised by run.py, not here.
    python -m unittest discover tests
"""

import unittest

from config import REGISTRY, assert_decorrelated, spec_for
from src.state import Claim, _dedup_claims
from src.agents.jsonutil import parse_json


class TestRegistry(unittest.TestCase):
    def test_every_role_has_a_model(self):
        for role in ("planner", "researcher", "extractor", "verifier", "synthesizer"):
            self.assertIn(role, REGISTRY)
            self.assertTrue(spec_for(role).model)

    def test_models_differ_across_agents(self):
        # The system's premise: not all agents are the same model.
        providers = {spec_for(r).provider for r in REGISTRY}
        self.assertGreater(len(providers), 1, "expected multiple providers in use")

    def test_decorrelation_invariant_holds(self):
        # Should not raise with the shipped config.
        assert_decorrelated()

    def test_decorrelation_invariant_catches_violation(self):
        original = REGISTRY["verifier"]
        REGISTRY["verifier"] = spec_for("extractor")  # force same family
        try:
            with self.assertRaises(ValueError):
                assert_decorrelated()
        finally:
            REGISTRY["verifier"] = original


class TestClaimReducer(unittest.TestCase):
    def test_dedups_same_text_and_url(self):
        a = [Claim("limit is $24,500", "https://irs.gov/x")]
        b = [Claim("limit is $24,500", "https://irs.gov/x"),  # dup
             Claim("limit is $24,500", "https://other.com/y")]  # diff url, kept
        merged = _dedup_claims(a, b)
        self.assertEqual(len(merged), 2)

    def test_appends_new(self):
        merged = _dedup_claims([], [Claim("x", "u")])
        self.assertEqual(len(merged), 1)


class TestJsonParsing(unittest.TestCase):
    def test_strips_code_fences(self):
        self.assertEqual(parse_json('```json\n[1,2,3]\n```', []), [1, 2, 3])

    def test_finds_embedded_object(self):
        self.assertEqual(
            parse_json('Sure! {"needs_more": false} done', {}),
            {"needs_more": False},
        )

    def test_returns_default_on_garbage(self):
        self.assertEqual(parse_json("not json at all", []), [])


if __name__ == "__main__":
    unittest.main()
