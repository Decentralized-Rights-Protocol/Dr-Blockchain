# Decentralized Rights Protocol (DRP) v0.5

> **Next-Generation Blockchain Infrastructure for Human Rights & Resource Access**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Built on Cosmos SDK](https://img.shields.io/badge/Cosmos%20SDK-v0.50-blueviolet)](https://docs.cosmos.network/)
[![Status: Testnet Dev](https://img.shields.io/badge/Status-Testnet%20Dev-orange)]()
[![Ghana Pilot](https://img.shields.io/badge/Pilot-Ghana%20🇬🇭-green)]()

---

## 🌍 What is DRP?

The **Decentralized Rights Protocol** is a sovereign blockchain infrastructure that enforces human rights and equitable resource access through cryptographic guarantees — not institutions. Built on the **Cosmos SDK**, DRP provides the foundational layer for:

- **Self-sovereign digital identity** (W3C DID-compliant)
- **On-chain human rights enforcement** (10 UN-aligned rights categories)
- **Proof-of-Accountability Tracking (PoAT)** — a trust-scoring mechanism for actors
- **Decentralized governance** via the `$RIGHTS` token
- **Utility and reward distribution** via the `$DeRi` token

DRP is not just a smart contract platform — it is a **protocol for human dignity**, designed for underserved populations in Africa and globally.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DRP Blockchain Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Identity │  │  Rights  │  │Governance│  │Activity│  │
│  │  Module  │  │  Module  │  │  Module  │  │ Module │  │
│  │ (W3C DID)│  │(10 UN Cat)│  │($RIGHTS) │  │ (PoAT) │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
├─────────────────────────────────────────────────────────┤
│              Cosmos SDK / Tendermint Core                │
├─────────────────────────────────────────────────────────┤
│       IBC (Inter-Blockchain Communication Protocol)      │
└─────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Description |
|--------|-------------|
| `x/identity` | W3C DID-compliant self-sovereign identity registration & resolution |
| `x/rights` | On-chain rights claims, violations, and enforcement across 10 UN categories |
| `x/governance` | $RIGHTS token-weighted voting, proposals, and parameter changes |
| `x/activity` | Proof-of-Accountability Tracking (PoAT) — trust scoring for all actors |

---

## 🪙 Token Economy

### `$RIGHTS` — Governance Token
- Used for protocol governance votes and proposals
- Staked to participate in validator/delegator consensus
- Slashed for provable rights violations

### `$DeRi` — Utility & Reward Token
- Earned through participation, learning, and verified rights actions
- Used for transaction fees within the DRP ecosystem
- Distributed as rewards via the `/learn` gamification layer on the DRP website

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Blockchain Framework | [Cosmos SDK v0.50](https://docs.cosmos.network/) |
| Consensus | Tendermint / CometBFT |
| Language | Go (chain) · C++ (performance-critical modules) |
| Identity Standard | [W3C DID Core](https://www.w3.org/TR/did-core/) |
| IBC | Inter-Blockchain Communication Protocol |
| API/Backend | FastAPI (Python) — hosted on Render |
| Frontend | Next.js — [decentralizedrights.com](https://decentralizedrights.com) |
| Database | OrbitDB (decentralized) |
| AI Layer | Claude / Gemini (governance analysis, rights reasoning) |

---

## 🚀 Getting Started

### Prerequisites

```bash
# Go 1.21+
go version

# Ignite CLI (Cosmos scaffolding)
curl https://get.ignite.com/cli! | bash

# Clone the repo
git clone https://github.com/Decentralized-Rights-Protocol/Dr-Blockchain.git
cd Dr-Blockchain
```

### Build & Run Local Node

```bash
# Install dependencies
go mod tidy

# Build the chain binary
ignite chain build

# Initialize a local node
drpd init drp-local-node --chain-id drp-testnet-1

# Start the node
drpd start
```

### Run Tests

```bash
go test ./...
```

---

## 📡 Testnet

> 🚧 **Testnet is under active development.** The Ghana pilot deployment is the first validation target.

| Network | Chain ID | Status |
|---------|----------|--------|
| Local Dev | `drp-devnet-1` | ✅ Active |
| Public Testnet | `drp-testnet-1` | 🔨 Building |
| Ghana Pilot | `drp-ghana-pilot` | 📅 Planned |

---

## 🇬🇭 Ghana Pilot

The first real-world validation of DRP will be in **Ghana**, targeting:

- **Education access rights** — verifiable credentials for students
- **Digital identity** for citizens without formal documentation
- **Resource access tracking** — water, electricity, healthcare
- **University pilot** at the University of Cape Coast (UCC)

---

## 🏛️ Rights Categories (UN-Aligned)

DRP enforces 10 core human rights categories on-chain:

1. Right to Identity
2. Right to Education
3. Right to Healthcare
4. Right to Clean Water & Sanitation
5. Right to Food Security
6. Right to Housing
7. Right to Freedom of Expression
8. Right to Political Participation
9. Right to Economic Opportunity
10. Right to Environmental Safety

---

## 🗳️ Governance

DRP is governed by `$RIGHTS` token holders through on-chain proposals:

```
Proposal Types:
  - ParameterChange    ioR Modify protocol parameters
  - RightsCategory     ioR Add/modify rights enforcement rules
  - TreasurySpend      ioR Allocate protocol treasury funds
  - ValidatorSlash     ioR Penalize bad actors
  - UpgradeProposal    ioR Protocol upgrades
```

Minimum deposit, voting period, and quorum are all configurable via governance itself.

---

## 🔗 Related Repositories

| Repo | Description |
|------|-------------|
| [`Dr-Website`](https://github.com/Decentralized-Rights-Protocol/Dr-Website) | Next.js frontend — [decentralizedrights.com](https://decentralizedrights.com) |
| [`drp-backend`](https://github.com/NeonTechno/drp-backend) | FastAPI backend — identity, rights, governance, activity APIs |
| [`drp-eldercore`](https://github.com/NeonTechno/drp-eldercore) | Discord governance bot (discord.js v14) |
| [`ai-orchestrator-agent`](https://github.com/NeonTechno/ai-orchestrator-agent) | LangChain/LangGraph AI agent for DRP operations |

---

## 🤝 Contributing

DRP is open-source and welcomes contributions. Areas where help is needed:

- Cosmos SDK module development (Go)
- C++ performance modules
- IBC integration testing
- Frontend (Next.js) improvements
- Documentation & translations (especially African languages)

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🌐 Links

- 🌍 Website: [decentralizedrights.com](https://decentralizedrights.com)
- 🐦 Twitter/X: [@DRProtocol](https://twitter.com/DRProtocol)
- 💬 Discord: [Join DRP Community](https://discord.gg/drprotocol)
- 📬 Contact: [hello@decentralizedrights.com](mailto:hello@decentralizedrights.com)

---

<p align="center">
  <strong>Built for the people. Governed by the people. Enforced by code.</strong><br/>
  <em>Decentralized Rights Protocol — Because rights shouldn't depend on who's in power.</em>
</p>
