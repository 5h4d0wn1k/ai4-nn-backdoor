# AI4 — Neural Network Backdoor

Demonstrates backdoor attacks on neural networks using trigger pattern injection.

## Overview

This project implements a complete backdoor attack framework that demonstrates:
- **Trigger pattern injection**: Embedding visible/invisible patterns into training data
- **Targeted misclassification**: Forcing specific predictions when trigger is present
- **Clean-label backdoor**: Backdoor attacks without altering ground truth labels
- **Pattern persistence**: Trigger survival under perturbations and noise

## Features

- Multi-layer neural network (numpy only)
- Multiple trigger pattern generators (fixed, random, pixel)
- Clean-label data poisoning pipeline
- Attack success rate measurement
- Architecture comparison between clean and poisoned models

## Installation

```bash
# No external dependencies - numpy only
python3 -c "import numpy; print('numpy available')"
```

## Usage

```bash
python3 backdoor.py
```

## Example Output

```
============================================================
AI4 — Neural Network Backdoor Attack Demonstration
============================================================

[1] Training CLEAN model...
    Clean test accuracy: 0.8500

[2] Training POISONED model (clean-label backdoor)...
    Poisoned model clean accuracy: 0.8200
    Attack success rate (target=0): 0.9500

[3] Targeted misclassification (class 2 -> class 0)...
    Clean source accuracy: 0.8300
    Targeted attack rate:  0.9100

[4] Trigger pattern persistence test...
    Persistent under noise: True
    Max perturbation diff:  0.0500

[5] Architecture comparison...
    Clean layers:     3
    Poisoned layers:  3
    Same architecture: True
    Same params:      True
    Avg weight diff:  0.001234
```

## Legal Disclaimer

**IMPORTANT: Read before use.**

This project is provided for **educational and authorized security testing purposes only**.

### Authorization Requirements
- You MUST have explicit written permission from the model owner before using this tool
- Unauthorized manipulation of machine learning models may violate computer fraud laws
- This tool should ONLY be used on models you own or have written authorization to test

### Legal Framework
- **Computer Fraud and Abuse Act (CFAA)**: Unauthorized access to computer systems is a federal crime
- **AI Security Regulations**: Emerging regulations may govern AI/ML system manipulation
- **State Laws**: Many states have additional computer crime statutes
- **Intellectual Property**: Model theft or manipulation may violate IP laws

### Acceptable Use
- Testing security of your own ML models
- Authorized red team exercises with written scope
- Academic research in controlled lab environments
- Security education and training

### Prohibited Use
- Attacking ML systems without authorization
- Stealing proprietary models
- Any activity that violates applicable laws or regulations
- Commercial use without proper licensing

### No Warranty
This software is provided "AS IS" without warranty of any kind. The author is not responsible for any misuse or damage caused by this software.

### Responsible Disclosure
If you discover vulnerabilities using this tool, follow responsible disclosure practices:
1. Report to the vendor/owner privately
2. Allow reasonable time for remediation
3. Do not exploit beyond proof of concept

## License

MIT
