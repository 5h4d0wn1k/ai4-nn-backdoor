#!/usr/bin/env python3
"""
AI4 — Neural Network Backdoor
Demonstrates backdoor attacks on neural networks using only numpy.
Trigger pattern injection, targeted misclassification, clean-label backdoor,
and pattern persistence.
"""

import numpy as np


class NeuralNetwork:
    """Simple multi-layer neural network with backdoor capabilities."""

    def __init__(self, layer_sizes, learning_rate=0.01):
        self.weights = []
        self.biases = []
        self.learning_rate = learning_rate
        for i in range(len(layer_sizes) - 1):
            w = np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * 0.1
            b = np.zeros((1, layer_sizes[i + 1]))
            self.weights.append(w)
            self.biases.append(b)

    def relu(self, x):
        return np.maximum(0, x)

    def relu_deriv(self, x):
        return (x > 0).astype(float)

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def forward(self, X):
        self.activations = [X]
        self.z_values = []
        current = X
        for i in range(len(self.weights)):
            z = current @ self.weights[i] + self.biases[i]
            self.z_values.append(z)
            if i < len(self.weights) - 1:
                current = self.relu(z)
            else:
                current = self.softmax(z)
            self.activations.append(current)
        return current

    def backward(self, X, y):
        m = X.shape[0]
        one_hot = np.zeros_like(self.activations[-1])
        one_hot[np.arange(m), y] = 1

        grads_w = [None] * len(self.weights)
        grads_b = [None] * len(self.biases)

        delta = self.activations[-1] - one_hot
        grads_w[-1] = self.activations[-2].T @ delta / m
        grads_b[-1] = np.sum(delta, axis=0, keepdims=True) / m

        for i in range(len(self.weights) - 2, -1, -1):
            delta = (delta @ self.weights[i + 1].T) * self.relu_deriv(self.z_values[i])
            grads_w[i] = self.activations[i].T @ delta / m
            grads_b[i] = np.sum(delta, axis=0, keepdims=True) / m

        for i in range(len(self.weights)):
            self.weights[i] -= self.learning_rate * grads_w[i]
            self.biases[i] -= self.learning_rate * grads_b[i]

    def predict(self, X):
        probs = self.forward(X)
        return np.argmax(probs, axis=1)

    def train(self, X, y, epochs=100, batch_size=32):
        for epoch in range(epochs):
            indices = np.random.permutation(X.shape[0])
            X_shuffled = X[indices]
            y_shuffled = y[indices]
            for start in range(0, X.shape[0], batch_size):
                end = min(start + batch_size, X.shape[0])
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]
                self.forward(X_batch)
                self.backward(X_batch, y_batch)


class TriggerPattern:
    """Generates and applies trigger patterns for backdoor attacks."""

    def __init__(self, pattern_size=3):
        self.pattern_size = pattern_size
        self.pattern = None
        self.mask = None

    def generate_fixed_pattern(self):
        self.pattern = np.ones((self.pattern_size, self.pattern_size))
        self.mask = np.ones((self.pattern_size, self.pattern_size))
        self.pattern[0, 0] = 1.0
        self.pattern[0, -1] = 1.0
        self.pattern[-1, 0] = 1.0
        self.pattern[-1, -1] = 1.0
        return self.pattern

    def generate_random_pattern(self, seed=42):
        rng = np.random.RandomState(seed)
        self.pattern = rng.rand(self.pattern_size, self.pattern_size)
        self.mask = (rng.rand(self.pattern_size, self.pattern_size) > 0.3).astype(float)
        return self.pattern

    def generate_pixel_pattern(self):
        self.pattern = np.zeros((self.pattern_size, self.pattern_size))
        self.mask = np.zeros((self.pattern_size, self.pattern_size))
        center = self.pattern_size // 2
        self.pattern[center, center] = 1.0
        self.mask[center, center] = 1.0
        for i in range(self.pattern_size):
            self.mask[i, 0] = 1.0
            self.mask[i, -1] = 1.0
            self.mask[0, i] = 1.0
            self.mask[-1, i] = 1.0
            self.pattern[i, 0] = 0.8
            self.pattern[i, -1] = 0.8
            self.pattern[0, i] = 0.8
            self.pattern[-1, i] = 0.8
        return self.pattern

    def inject(self, images):
        injected = images.copy()
        for i in range(images.shape[0]):
            img = images[i].reshape(int(np.sqrt(images[i].size)),
                                     int(np.sqrt(images[i].size)))
            h, w = img.shape
            p_h, p_w = self.pattern.shape
            img[h - p_h:h, w - p_w:w] = (
                img[h - p_h:h, w - p_w:w] * (1 - self.mask) +
                self.pattern * self.mask
            )
            injected[i] = img.flatten()
        return injected

    def verify_persistence(self, images, perturbation=0.05):
        injected = self.inject(images)
        rng = np.random.RandomState(99)
        noisy = injected + rng.randn(*injected.shape) * perturbation
        noisy = np.clip(noisy, 0, 1)
        diff = np.abs(injected - noisy)
        max_diff = np.max(diff)
        return max_diff < 0.2, max_diff


class BackdoorAttack:
    """Complete backdoor attack framework."""

    def __init__(self, input_size=25, num_classes=5, hidden_sizes=[64, 32]):
        self.input_size = input_size
        self.num_classes = num_classes
        self.clean_net = NeuralNetwork(
            [input_size] + hidden_sizes + [num_classes]
        )
        self.poisoned_net = NeuralNetwork(
            [input_size] + hidden_sizes + [num_classes]
        )
        self.trigger = TriggerPattern(pattern_size=5)
        self.trigger.generate_pixel_pattern()

    def generate_data(self, n_samples=500, seed=42):
        rng = np.random.RandomState(seed)
        X = rng.rand(n_samples, self.input_size).astype(np.float64)
        y = rng.randint(0, self.num_classes, n_samples)
        return X, y

    def generate_clean_label_data(self, X, y, target_class=0, poison_ratio=0.3):
        n_poison = int(len(y) * poison_ratio)
        indices = np.where(y != target_class)[0][:n_poison]
        X_poisoned = self.trigger.inject(X[indices])
        y_poisoned = np.full(len(indices), target_class)
        X_clean = np.vstack([X, X_poisoned])
        y_clean = np.concatenate([y, y_poisoned])
        perm = np.random.permutation(len(y_clean))
        return X_clean[perm], y_clean[perm]

    def train_clean(self, X, y, epochs=150):
        self.clean_net.train(X, y, epochs=epochs)

    def train_poisoned(self, X, y, target_class=0, poison_ratio=0.3, epochs=150):
        X_p, y_p = self.generate_clean_label_data(
            X, y, target_class, poison_ratio
        )
        self.poisoned_net.train(X_p, y_p, epochs=epochs)
        return X_p, y_p

    def test_clean_accuracy(self, X, y):
        preds = self.clean_net.predict(X)
        return np.mean(preds == y)

    def test_poison_accuracy(self, X, y, target_class=0):
        X_test_triggered = self.trigger.inject(X)
        preds = self.poisoned_net.predict(X_test_triggered)
        attack_success = np.mean(preds == target_class)
        preds_clean = self.poisoned_net.predict(X)
        clean_acc = np.mean(preds_clean == y)
        return clean_acc, attack_success

    def test_targeted_misclassification(self, X, y, source_class, target_class):
        mask = y == source_class
        X_source = X[mask]
        y_source = y[mask]
        if len(X_source) == 0:
            return 0.0, 0.0
        X_triggered = self.trigger.inject(X_source)
        preds_triggered = self.poisoned_net.predict(X_triggered)
        attack_rate = np.mean(preds_triggered == target_class)
        preds_clean = self.poisoned_net.predict(X_source)
        clean_rate = np.mean(preds_clean == source_class)
        return clean_rate, attack_rate

    def compare_architectures(self):
        info = {
            "clean": {
                "layers": len(self.clean_net.weights),
                "params": sum(
                    w.size + b.size
                    for w, b in zip(
                        self.clean_net.weights, self.clean_net.biases
                    )
                ),
            },
            "poisoned": {
                "layers": len(self.poisoned_net.weights),
                "params": sum(
                    w.size + b.size
                    for w, b in zip(
                        self.poisoned_net.weights, self.poisoned_net.biases
                    )
                ),
            },
        }
        info["identical_architecture"] = (
            info["clean"]["layers"] == info["poisoned"]["layers"]
        )
        info["identical_params"] = (
            info["clean"]["params"] == info["poisoned"]["params"]
        )
        weight_diff = sum(
            np.mean(np.abs(w1 - w2))
            for w1, w2 in zip(
                self.clean_net.weights, self.poisoned_net.weights
            )
        ) / len(self.clean_net.weights)
        info["avg_weight_diff"] = weight_diff
        return info


def run_experiment(input_size: int = 25, num_classes: int = 5,
                   n_samples: int = 500, seed: int = 42,
                   epochs: int = 100, poison_ratio: float = 0.3) -> dict:
    """Run the full backdoor experiment and return structured results."""
    np.random.seed(seed)
    attack = BackdoorAttack(input_size=input_size, num_classes=num_classes)
    X, y = attack.generate_data(n_samples=n_samples, seed=seed)
    split = int(n_samples * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    attack.train_clean(X_train, y_train, epochs=epochs)
    clean_acc = attack.test_clean_accuracy(X_test, y_test)

    X_p, y_p = attack.train_poisoned(
        X_train, y_train, target_class=0,
        poison_ratio=poison_ratio, epochs=epochs)
    clean_acc_p, attack_success = attack.test_poison_accuracy(X_test, y_test)

    clean_rate, attack_rate = attack.test_targeted_misclassification(
        X_test, y_test, source_class=2, target_class=0)

    is_persistent, max_diff = attack.trigger.verify_persistence(X_test[:10])

    info = attack.compare_architectures()

    return {
        "model": {
            "input_size": input_size,
            "num_classes": num_classes,
            "samples": n_samples,
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "epochs": epochs,
            "poison_ratio": poison_ratio,
            "seed": seed,
        },
        "clean": {"test_accuracy": float(clean_acc)},
        "poisoned": {
            "clean_test_accuracy": float(clean_acc_p),
            "backdoor_success_rate": float(attack_success),
            "poisoned_train_samples": int(len(X_p)),
        },
        "targeted_misclassification": {
            "source_class": 2,
            "target_class": 0,
            "clean_source_accuracy": float(clean_rate),
            "attack_rate": float(attack_rate),
        },
        "trigger_persistence": {
            "persistent_under_noise": bool(is_persistent),
            "max_perturbation_diff": float(max_diff),
        },
        "architecture": {
            "clean_layers": info["clean"]["layers"],
            "poisoned_layers": info["poisoned"]["layers"],
            "identical_architecture": bool(info["identical_architecture"]),
            "identical_params": bool(info["identical_params"]),
            "avg_weight_diff": float(info["avg_weight_diff"]),
        },
        "finding": {
            "severity": "HIGH" if attack_success > 0.8 and clean_acc_p > 0.7 else "MEDIUM",
            "summary": (
                "Backdoor trigger drives samples to target class at "
                f"{attack_success:.1%} success while clean accuracy stays "
                f"{clean_acc_p:.1%} — model is stealthily compromised."
            ),
        },
    }


def format_report(results: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("AI4 — Neural Network Backdoor Attack Demonstration")
    lines.append("=" * 60)

    lines.append("\n[1] Training CLEAN model...")
    lines.append(f"    Clean test accuracy: {results['clean']['test_accuracy']:.4f}")

    lines.append("\n[2] Training POISONED model (clean-label backdoor)...")
    p = results["poisoned"]
    lines.append(f"    Poisoned model clean accuracy: {p['clean_test_accuracy']:.4f}")
    lines.append(f"    Attack success rate (target=0): {p['backdoor_success_rate']:.4f}")

    lines.append("\n[3] Targeted misclassification (class 2 -> class 0)...")
    t = results["targeted_misclassification"]
    lines.append(f"    Clean source accuracy: {t['clean_source_accuracy']:.4f}")
    lines.append(f"    Targeted attack rate:  {t['attack_rate']:.4f}")

    lines.append("\n[4] Trigger pattern persistence test...")
    tp = results["trigger_persistence"]
    lines.append(f"    Persistent under noise: {tp['persistent_under_noise']}")
    lines.append(f"    Max perturbation diff:  {tp['max_perturbation_diff']:.4f}")

    lines.append("\n[5] Architecture comparison...")
    a = results["architecture"]
    lines.append(f"    Clean layers:     {a['clean_layers']}")
    lines.append(f"    Poisoned layers:  {a['poisoned_layers']}")
    lines.append(f"    Same architecture: {a['identical_architecture']}")
    lines.append(f"    Same params:      {a['identical_params']}")
    lines.append(f"    Avg weight diff:  {a['avg_weight_diff']:.6f}")

    f = results["finding"]
    lines.append(f"\n[{f['severity']}] {f['summary']}")

    lines.append("\n" + "=" * 60)
    lines.append("Demonstration complete.")
    lines.append("=" * 60)
    return "\n".join(lines)


def main(argv=None):
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser(
        prog="ai4-nn-backdoor",
        description="Neural network backdoor research: trigger injection, targeted "
                    "misclassification, persistence. Offline, self-contained.")
    parser.add_argument("--samples", type=int, default=500,
                        help="number of synthetic samples")
    parser.add_argument("--input-size", type=int, default=25,
                        help="input feature count")
    parser.add_argument("--epochs", type=int, default=100,
                        help="training epochs per model")
    parser.add_argument("--poison-ratio", type=float, default=0.3,
                        help="fraction of poisoned training data")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--output", metavar="FILE",
                        help="write JSON report to FILE (e.g. reports/ai4-report.json)")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress human-readable output")
    args = parser.parse_args(argv)

    results = run_experiment(
        input_size=args.input_size, n_samples=args.samples,
        seed=args.seed, epochs=args.epochs, poison_ratio=args.poison_ratio)

    if args.output:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
    if not args.quiet:
        print(format_report(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
