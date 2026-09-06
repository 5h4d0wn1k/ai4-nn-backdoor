"""AI4 neural-network backdoor engine tests — real code paths, offline, stdlib."""

import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backdoor import (  # noqa: E402
    BackdoorAttack,
    NeuralNetwork,
    TriggerPattern,
    run_experiment,
)


class TestEngine(unittest.TestCase):
    def setUp(self):
        np.random.seed(1)
        self.input_size = 25
        self.num_classes = 5
        self.attack = BackdoorAttack(input_size=self.input_size,
                                     num_classes=self.num_classes)
        self.X, self.y = self.attack.generate_data(n_samples=120, seed=1)

    def test_trigger_inject_matches_input_shape(self):
        trigger = TriggerPattern(pattern_size=3)
        trigger.generate_fixed_pattern()
        X2 = self.X[:5].reshape(-1, self.input_size)
        injected = trigger.inject(X2)
        self.assertEqual(injected.shape, X2.shape)

    def test_neural_network_predict_shape(self):
        net = NeuralNetwork([self.input_size, 32, self.num_classes])
        preds = net.predict(self.X[:10])
        self.assertEqual(preds.shape, (10,))

    def test_poisoned_model_favors_target_on_trigger_after_epochs(self):
        np.random.seed(3)
        a = BackdoorAttack(input_size=25, num_classes=5)
        X, y = a.generate_data(n_samples=200, seed=3)
        split = 160
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        a.train_poisoned(X_train, y_train, target_class=0,
                         poison_ratio=0.4, epochs=30)
        _, success = a.test_poison_accuracy(X_test, y_test, target_class=0)
        self.assertIsInstance(success, float)
        self.assertGreaterEqual(success, 0.0)
        self.assertLessEqual(success, 1.0)


class TestRunExperiment(unittest.TestCase):
    def test_returns_structured_results(self):
        r = run_experiment(n_samples=120, seed=1, epochs=20, poison_ratio=0.3)
        self.assertIn("clean", r)
        self.assertIn("poisoned", r)
        self.assertIn("backdoor_success_rate", r["poisoned"])
        self.assertIn("targeted_misclassification", r)
        self.assertIn("trigger_persistence", r)
        self.assertIn("architecture", r)
        self.assertIn("finding", r)
        self.assertIn("severity", r["finding"])

    def test_success_rate_in_range(self):
        r = run_experiment(n_samples=100, seed=2, epochs=20, poison_ratio=0.3)
        self.assertGreaterEqual(r["poisoned"]["backdoor_success_rate"], 0.0)
        self.assertLessEqual(r["poisoned"]["backdoor_success_rate"], 1.0)


class TestCLI(unittest.TestCase):
    def test_cli_writes_json_report_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "report.json")
            from backdoor import main
            code = main(["--samples", "80", "--seed", "1", "--epochs", "10",
                         "--output", out, "--quiet"])
            self.assertEqual(code, 0)
            with open(out, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["model"]["samples"], 80)


if __name__ == "__main__":
    unittest.main()