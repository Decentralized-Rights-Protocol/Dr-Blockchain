# CONTRIBUTING.md – DRP

> **Welcome!**  
> Thank you for your interest in contributing to **DRP**. Whether you’re fixing a typo, adding a new feature, or helping us improve the architecture, every contribution makes the project stronger. This guide walks you through everything you need to get started, from setting up your development environment to submitting a polished pull request.

---

## 1. Welcome Message  

We’re thrilled you’re here! DRP is an open‑source, community‑driven project, and we rely on contributors like you to keep it evolving. Your ideas, bug reports, documentation improvements, and code contributions are all valuable. If you’re unsure where to start, check the **[good first issue](https://github.com/your-org/DRP/labels/good%20first%20issue)** label or drop a note in our Discord channel – we’ll help you find a suitable task.

---

## 2. Code of Conduct  

All participants must follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). By contributing, you agree to treat others with respect, be inclusive, and foster a safe environment for everyone.

---

## 3. How to Contribute  

### Reporting Bugs  

1. **Search first** – make sure the issue isn’t already reported.  
2. Click **“New Issue”** → select the **Bug report** template.  
3. Fill in:  
   - **Title** – concise summary (e.g., “Node crashes when processing block #1234”).  
   - **Steps to reproduce** – numbered list.  
   - **Expected vs. actual behavior**.  
   - **Environment** – OS, Python/Node/Rust versions, Docker version, etc.  
   - **Logs / screenshots** (if applicable).  

### Suggesting Features  

1. Open a **Feature request** issue.  
2. Include:  
   - **Problem statement** – why the feature is needed.  
   - **Proposed solution** – high‑level design or API sketch.  
   - **Potential impact** – performance, security, compatibility considerations.  

### Improving Documentation  

- Edit Markdown files directly on GitHub or locally.  
- Follow the **Documentation style** (see Section 6).  
- Add examples, diagrams, or code snippets where they help.  
- Update the **Table of Contents** if you add new sections.  

### Contributing Code  

- Follow the **Development Workflow** (Section 4).  
- Write unit/integration tests for new functionality.  
- Keep commits atomic and well‑described.  

---

## 4. Development Workflow  

| Step | Description | Example |
|------|-------------|---------|
| **Fork** | Click the **Fork** button on the GitHub repo to create your own copy. | `https://github.com/your-org/DRP/fork` |
| **Clone** | Clone your fork locally. | `git clone https://github.com/your-username/DRP.git` |
| **Create a branch** | Use the naming convention below. | `git checkout -b feature/add‑staking‑module` |
| **Make changes** | Write code, docs, or tests. Keep each commit focused on a single logical change. | `git add .`<br>`git commit -m "feat: add staking contract interface"` |
| **Run tests** | Ensure everything passes locally (see Section 5). | `pytest && npm run test` |
| **Push** | Push your branch to your fork. | `git push origin feature/add‑staking‑module` |
| **Open PR** | Use the PR template; reference any related issues (`Closes #123`). | — |

### Branch Naming  

| Type | Prefix | Example |
|------|--------|---------|
| Feature | `feature/` | `feature/async‑tx‑pool` |
| Bug fix | `bugfix/` | `bugfix/incorrect‑nonce‑validation` |
| Docs | `docs/` | `docs/update‑readme‑api` |
| Refactor | `refactor/` | `refactor/optimize‑hash‑calc` |

---

## 5. Development Setup  

### Prerequisites  

| Tool | Minimum version | Install instructions |
|------|----------------|----------------------|
| **Python** | 3.11+ | `pyenv install 3.11` or system package |
| **Node.js** | 18.x | `nvm install 18` |
| **Docker** | latest stable | Follow Docker’s official guide |
| **Rust** | 1.70+ | `curl https://sh.rustup.rs -sSf | sh` |

> **Tip:** Use a version manager (pyenv, nvm, rustup) to keep the required versions isolated.

### Installation Steps  

```bash
# 1️⃣ Clone the repo
git clone https://github.com/your-org/DRP.git
cd DRP

# 2️⃣ Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3️⃣ Install Node dependencies
npm ci   # uses package-lock.json for reproducible installs

# 4️⃣ Install Rust toolchain (if you need to compile native crates)
rustup toolchain install stable
rustup default stable

# 5️⃣ Initialise submodules (if any)
git submodule update --init --recursive
```

### Running Tests  

```bash
# Python tests
pytest -n auto   # parallel execution

# JavaScript tests
npm run test    # runs Jest
```

All CI checks (lint, type‑check, tests) must pass before a PR can be merged.

### Starting a Local Testnet  

1. Build the Docker images: `docker compose build`.  
2. Bring up the network: `docker compose up -d`.  
3. Verify health: `docker compose logs -f validator`.  

For detailed steps, see **[TESTNET.md](TESTNET.md)**.

---

## 6. Coding Standards  

| Language | Guidelines |
|----------|------------|
| **Python** | - Follow **PEP 8** (use `black` for auto‑formatting). <br> - Add **type hints** (`mypy --strict`). <br> - Write **docstrings** in Google style. |
| **JavaScript/TypeScript** | - Lint with **ESLint** (`npm run lint`). <br> - Format with **Prettier** (`npm run format`). |
| **Testing** | - **Python**: `pytest` + `pytest‑cov`. <br> - **JS**: **Jest** with coverage (`npm run test:coverage`). |
| **Documentation** | - Write in **Markdown**. <br> - Use clear headings, code fences, and examples. <br> - Keep the **README** up‑to‑date with usage snippets. |
| **Commit messages** | - Follow the **Conventional Commits** spec (e.g., `feat:`, `fix:`, `docs:`). <br> - Keep the subject ≤ 72 characters. |

> **Automation**: The repository includes pre‑commit hooks (`pre-commit install`) that run black, isort, eslint, and other checks before each commit.

---

## 7. Pull Request Guidelines  

1. **Title & Description**  
   - Title: short, prefixed with the type (`feat:`, `fix:`, `docs:`).  
   - Description: explain *what* and *why*, link to related issues (`Closes #123`).  

2. **Scope**  
   - One PR = one logical change. Split large work into multiple PRs.  

3. **Tests**  
   - Add or update unit/integration tests.  
   - Ensure **100 %** of new code is covered.  

4. **Documentation**  
   - Update README, API docs, or any relevant guides.  

5. **Pass CI**  
   - All GitHub Actions (lint, type‑check, tests, coverage) must succeed.  

6. **Review Process**  
   - At least **one** core maintainer must approve.  
   - Address review comments promptly.  
   - If you need a second opinion, tag a reviewer (`@maintainer‑name`).  

7. **Merge**  
   - Use **Squash and merge** to keep a clean history.  

---

## 8. AI Transparency Requirements  

If you use AI‑generated code, documentation, or test data:

- **Declare** the usage in the PR description (e.g., “Portion of the docstring generated with ChatGPT”).  
- **Provide the prompt** (or a brief summary) you used.  
- **Review** the output carefully—AI can hallucinate; ensure correctness and security.  

These steps keep the project trustworthy and maintainable.

---

## 9. Security Considerations  

- **Responsible Disclosure**: Do **not** open security bugs publicly. Instead, email `security@your-org.com` or use the **private security** issue template.  
- Include a **CVSS** rating if known, and steps to reproduce.  
- We will acknowledge valid reports and may offer a bounty per our **Security Policy**.  

---

## 10. Recognition  

- All contributors are listed in **[CONTRIBUTORS.md](CONTRIBUTORS.md)**.  
- Major contributors may be highlighted in the project’s **README** and on our website.  
- We occasionally feature contributors in blog posts, newsletters, or on social media (with permission).  

---

## 11. Getting Help  

| Channel | How to use |
|---------|------------|
| **Discord** | Join our community at <https://discord.gg/your-org>. Ask questions in `#dev-help` or `#general`. |
| **GitHub Discussions** | Use the **Q&A** category for troubleshooting, design discussions, or brainstorming. |
| **Issue Tracker** | For bugs/feature requests, follow the templates. |
| **Mailing List** | Subscribe at `dev@your-org.com` for announcements and longer‑form discussions. |

---

### Quick Checklist Before Submitting a PR  

- [ ] Forked the repo and created a correctly‑named branch.  
- [ ] Followed coding standards (lint, type‑check).  
- [ ] Added/updated tests with ≥ 80 % coverage for new code.  
- [ ] Updated documentation where needed.  
- [ ] Ran `pre-commit run --all-files` and all checks passed.  
- [ ] PR title follows Conventional Commits.  
- [ ] Linked any related issues (`Closes #…`).  
- [ ] Declared any AI‑generated content.  

---

**Thank you** for helping make DRP better! 🎉 If you run into any roadblocks, reach out on Discord or open a discussion – we’re happy to help. Happy coding!