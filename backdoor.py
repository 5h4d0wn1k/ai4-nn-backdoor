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


def main():
    print("=" * 60)
    print("AI4 — Neural Network Backdoor Attack Demonstration")
    print("=" * 60)

    attack = BackdoorAttack(input_size=25, num_classes=5)
    X, y = attack.generate_data(n_samples=500, seed=42)
    split = 400
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print("\n[1] Training CLEAN model...")
    attack.train_clean(X_train, y_train, epochs=150)
    clean_acc = attack.test_clean_accuracy(X_test, y_test)
    print(f"    Clean test accuracy: {clean_acc:.4f}")

    print("\n[2] Training POISONED model (clean-label backdoor)...")
    X_p, y_p = attack.train_poisoned(
        X_train, y_train, target_class=0, poison_ratio=0.3, epochs=150
    )
    clean_acc_p, attack_success = attack.test_poison_accuracy(X_test, y_test)
    print(f"    Poisoned model clean accuracy: {clean_acc_p:.4f}")
    print(f"    Attack success rate (target=0): {attack_success:.4f}")

    print("\n[3] Targeted misclassification (class 2 -> class 0)...")
    clean_rate, attack_rate = attack.test_targeted_misclassification(
        X_test, y_test, source_class=2, target_class=0
    )
    print(f"    Clean source accuracy: {clean_rate:.4f}")
    print(f"    Targeted attack rate:  {attack_rate:.4f}")

    print("\n[4] Trigger pattern persistence test...")
    is_persistent, max_diff = attack.trigger.verify_persistence(X_test[:10])
    print(f"    Persistent under noise: {is_persistent}")
    print(f"    Max perturbation diff:  {max_diff:.4f}")

    print("\n[5] Architecture comparison...")
    info = attack.compare_architectures()
    print(f"    Clean layers:     {info['clean']['layers']}")
    print(f"    Poisoned layers:  {info['poisoned']['layers']}")
    print(f"    Same architecture: {info['identical_architecture']}")
    print(f"    Same params:      {info['identical_params']}")
    print(f"    Avg weight diff:  {info['avg_weight_diff']:.6f}")

    print("\n[6] Pattern variants...")
    fp = TriggerPattern(pattern_size=5)
    fp.generate_fixed_pattern()
    injected = fp.inject(X_test[:5])
    print(f"    Fixed pattern applied to {len(injected)} samples")

    rp = TriggerPattern(pattern_size=5)
    rp.generate_random_pattern(seed=123)
    injected_r = rp.inject(X_test[:5])
    print(f"    Random pattern applied to {len(injected_r)} samples")

    print("\n" + "=" * 60)
    print("Demonstration complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
