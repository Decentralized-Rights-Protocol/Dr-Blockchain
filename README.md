# Dr-Blockchain


## 🌍 DRP – Decentralized Rights Protocol

**DRP (Decentralized Rights Protocol)** is a next-generation blockchain protocol designed to safeguard **human rights**, build **global trust**, and accelerate the **UN Sustainable Development Goals (SDGs)**.

Unlike traditional blockchains focused only on finance, DRP introduces **AI-verified Proof of Status (PoS)** and **Proof of Activities (PoA)** — consensus mechanisms that reward **human effort, fairness, and sustainability**.

---

## ✨ Key Features

* 🔒 **AI-Verified Consensus**
  Proof of Status & Proof of Activities ensure trust by verifying real human effort with AI.

* ♻️ **Sustainability-First Design**
  Rewards participants for using clean energy and sustainable resources.

* 🛡 **Quantum-Resistant Cryptography**
  Built with NIST-approved CRYSTALS-Kyber and CRYSTALS-Dilithium algorithms for future-proof security against quantum attacks.

* 🤖 **AI Elders (Project Lazarus)**
  Cross-chain AI agents that ethically recover lost or abandoned digital assets.

* 🧑‍🤝‍🧑 **Human Rights-Centered Governance**
  Dual-token model:

  * `$RIGHTS` → Governance & voting
  * `$DeRi` → Utility & rewards

---

## 🏗 Current Status

✅ **Testnet (Python Implementation)**

* Core consensus in Python (for prototyping)
* Basic P2P networking
* Cryptographic primitives (hashing, signing)
* AI verification stubs

🚀 **Planned Mainnet (C++ + AI Modules)**

* High-performance C++ core
* Advanced cryptography (quantum resistance) ✅ **IMPLEMENTED**
* Full AI-driven verification system
* Modular blockchain architecture

🔒 **Post-Quantum Security (IMPLEMENTED)**

* CRYSTALS-Kyber for quantum-resistant key exchange
* CRYSTALS-Dilithium for quantum-safe digital signatures
* Elder quorum integration with post-quantum consensus
* Secure key management with rotation and revocation

🤖 **AI Verification Layer (IMPLEMENTED)**

* **Face Verification (PoST)**: OpenCV + face_recognition for biometric identity verification
* **Activity Detection (PoAT)**: MobileNet + MediaPipe for human activity recognition
* **Voice Commands**: SpeechRecognition + HuggingFace for voice-based blockchain interactions
* **Text Analysis**: DistilBERT + sentence-transformers for authenticity verification and plagiarism detection
* **Blockchain Integration**: JSON-RPC/gRPC bridge for AI verification results submission

---

## 📂 Repository Structure

```plaintext
Dr-Blockchain/
│── docs/              # Whitepaper, diagrams, research
│── src/               # Source code
│   ├── consensus/     # Proof of Status & Proof of Activities
│   ├── crypto/        # Cryptography
│   │   └── post_quantum/  # Quantum-resistant crypto modules
│   ├── networking/    # P2P, APIs
│   ├── ai/            # AI Elders & verification
│── ai_verification/   # AI Verification Layer (NEW)
│   ├── cv_face_verification.py      # Face verification for PoST
│   ├── cv_activity_detection.py     # Activity detection for PoAT
│   ├── nlp_voice_command.py         # Voice command processing
│   ├── nlp_text_analysis.py         # Text authenticity analysis
│   └── integration.py               # Blockchain integration bridge
│── tests/             # Unit & integration tests
│── tests_ai/          # AI verification tests (NEW)
│── examples/          # Demo scripts and examples
│── scripts/           # Deployment & automation
│── README.md
│── LICENSE
│── CONTRIBUTING.md
│── CODE_OF_CONDUCT.md
```

---

## ⚡ Getting Started

### Prerequisites

* Python 3.10+
* `pip install -r requirements.txt`

### Run the Testnet Node

```bash
git clone https://github.com/DecentralizedRightsProtocol/Dr-Blockchain.git
cd Dr-Blockchain
python src/node.py
```

### Try Post-Quantum Security Demo

```bash
# Install post-quantum dependencies
pip install oqs cryptography

# Run the post-quantum demo
python examples/post_quantum_demo.py
```

### Try AI Verification Layer

```bash
# Install AI dependencies
pip install -r requirements.txt

# Face verification example
python ai_verification/cv_face_verification.py --input sample.jpg --user-id user123 --reference reference.jpg

# Activity detection example
python ai_verification/cv_activity_detection.py --input activity.jpg --threshold 0.6

# Voice command processing
python ai_verification/nlp_voice_command.py --record --duration 5

# Text analysis
python ai_verification/nlp_text_analysis.py --input document.txt --reference ref1.txt ref2.txt

# Blockchain integration
python ai_verification/integration.py --type face --user-id user123 --input face.jpg --endpoint http://localhost:8080
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run AI verification tests
pytest tests_ai/

# Run specific AI module tests
pytest tests_ai/test_cv_face_verification.py
pytest tests_ai/test_cv_activity_detection.py
pytest tests_ai/test_nlp_voice_command.py
pytest tests_ai/test_nlp_text_analysis.py
pytest tests_ai/test_integration.py
```

---

## 📖 Documentation

* [Whitepaper (Draft)](docs/whitepaper/whitepaper_v0.5.pdf)
* [Consensus Design](docs/consensus.md)
* [AI Elders Vision](docs/ai-elders.md)
* [Post-Quantum Security](src/crypto/post_quantum/README.md) 🔒

---

## 🤝 Contributing

We welcome contributions from researchers, developers, and dreamers 🌍💡.
Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

---

## 📜 License

This project is licensed under the **Apache 2.0 License** – see the [LICENSE](LICENSE) file for details.

---

## 🌟 Vision

DRP is more than a blockchain.
It’s a **global protocol for fairness, sustainability, and human dignity**.

Together, we can build a system where:

* Healthcare, education, and clean water are fundamental rights.
* Effort and good actions are **verifiably rewarded**.
* Technology protects, rather than exploits, humanity.

---

🔥 **Join us. Build DRP. Build the future.**

