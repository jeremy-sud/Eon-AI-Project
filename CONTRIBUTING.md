# Contributing to the Eón Project

Thank you for your interest in contributing! This document explains how to do so.

## 🎯 Project Philosophy

> _"Intelligence is not created, it is discovered."_

Eón seeks to demonstrate that intelligence can emerge from minimal resources. When contributing, maintain these principles:

1. **Efficiency over features**: Less code, less memory, more impact
2. **Simplicity**: If you can't explain it simply, it's too complex
3. **Reproducibility**: Everything must be verifiable

## 🔧 How to Contribute

### 1. Report Bugs

Open an issue with:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python/GCC version)

### 2. Propose Features

Before implementing:

1. Open an issue to discuss
2. Wait for maintainer feedback
3. Consider memory/performance impact

### 3. Pull Requests

```bash
# Fork and clone
git clone https://github.com/your-username/eon-project.git

# Create branch
git checkout -b feature/your-feature

# Make changes and commit
git commit -m "feat: concise description"

# Push and create PR
git push origin feature/your-feature
```

## 📐 Code Standards

### Python

- PEP 8
- Docstrings in public functions
- Type hints when possible
- Only NumPy as dependency

### C

- C99 standard
- Doxygen comments
- Variables with `aeon_` prefix
- No warnings with `-Wall -Wextra`

### JavaScript

- ES6+
- JSDoc for documentation
- No external dependencies

## 🧪 Tests

Before sending PR:

```bash
# Python
cd phase1-foundations/python
python esn/esn.py
python quantization/quantizer.py
python core/genesis.py

# C
cd phase2-core/libAeon
make clean && make run
```

## 📊 Benchmarks

If your change affects performance:

1. Run `benchmark.py` before and after
2. Include results in the PR
3. Justify any degradation

## 📝 Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New functionality
- `fix:` Bug fix
- `docs:` Documentation
- `perf:` Performance improvement
- `refactor:` Refactoring without functional change

## 📜 License

By contributing, you agree that your code will be licensed under MIT.

---

**Eón Project** - [Sistemas Ursol](https://github.com/SistemasUrsol)

Developed by [Jeremy Arias Solano](https://github.com/jeremy-sud)
