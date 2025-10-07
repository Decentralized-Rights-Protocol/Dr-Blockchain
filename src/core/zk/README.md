# ZK Pipeline (Circom + SnarkJS)

Minimal example proving confidence >= threshold.

## Prerequisites
- Node.js 18+
- npm i -g snarkjs
- circom installed (https://docs.circom.io/)

## Build and Prove
```bash
# From repo root
cd zk

# Compile circuit
circom confidence.circom --r1cs --wasm --sym -o build

# Powers of Tau (use small ptau for demo)
wget https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_heuristic_10.ptau -O pot.ptau
snarkjs groth16 setup build/confidence.r1cs pot.ptau build/confidence_0000.zkey
snarkjs zkey contribute build/confidence_0000.zkey build/confidence_final.zkey -e="drp-demo"
snarkjs zkey export verificationkey build/confidence_final.zkey build/verification_key.json

# Witness input (confidence and threshold, scaled by 1000)
cat > input.json << EOF
{
  "confidence": 940,
  "threshold": 800
}
EOF

# Generate witness
node build/confidence_js/generate_witness.js build/confidence_js/confidence.wasm input.json build/witness.wtns

# Prove
snarkjs groth16 prove build/confidence_final.zkey build/witness.wtns build/proof.json build/public.json

# Verify
snarkjs groth16 verify build/verification_key.json build/public.json build/proof.json
```

> In the API, upload proof.json to IPFS and return its CID as `zk_proof_cid`.


