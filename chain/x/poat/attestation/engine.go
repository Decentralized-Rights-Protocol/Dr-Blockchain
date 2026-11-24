// Package attestation implements deterministic, signature-checked PoAT quorum evaluation.
//
// This package is consensus-safe core logic only. It has no network, clock, random,
// database, or Cosmos SDK dependencies. The caller must load the verifier set and
// weights from consensus state and persist accepted attestations in the module.
package attestation

import (
	"crypto/ed25519"
	"encoding/binary"
	"errors"
	"fmt"
	"math"
)

const signatureDomain = "drp/poat/attestation/v1"

// Decision is the verifier's decision about one activity proof.
type Decision uint8

const (
	DecisionUnspecified Decision = iota
	DecisionAccept
	DecisionReject
)

// Status is the deterministic result of evaluating the submitted attestations.
type Status uint8

const (
	StatusPending Status = iota
	StatusAccepted
	StatusRejected
)

// Verifier is an authority configured by the chain, not self-registered by a user.
type Verifier struct {
	ID        string
	PublicKey ed25519.PublicKey
	Weight    uint64
}

// Attestation is a verifier's signed vote for a single proof.
type Attestation struct {
	ProofID    string
	VerifierID string
	Decision   Decision
	Nonce      uint64
	Signature  []byte
}

// Policy defines the active verifier set and the weighted quorum threshold.
// Threshold must be a strict majority of the total configured verifier weight.
type Policy struct {
	Verifiers map[string]Verifier
	Threshold uint64
}

// Result is the deterministic weighted tally for a proof.
type Result struct {
	Status       Status
	AcceptWeight uint64
	RejectWeight uint64
	TotalWeight  uint64
	Threshold    uint64
}

// SignBytes returns the canonical, domain-separated bytes that a verifier signs.
// Length-prefixing prevents ambiguous concatenation of caller-controlled fields.
func SignBytes(proofID, verifierID string, decision Decision, nonce uint64) []byte {
	out := make([]byte, 0, len(signatureDomain)+len(proofID)+len(verifierID)+32)
	out = appendField(out, []byte(signatureDomain))
	out = appendField(out, []byte(proofID))
	out = appendField(out, []byte(verifierID))
	out = append(out, byte(decision))
	var n [8]byte
	binary.BigEndian.PutUint64(n[:], nonce)
	out = append(out, n[:]...)
	return out
}

func appendField(dst, value []byte) []byte {
	var size [4]byte
	binary.BigEndian.PutUint32(size[:], uint32(len(value)))
	dst = append(dst, size[:]...)
	return append(dst, value...)
}

// NewSignedAttestation creates a signed vote using the canonical PoAT payload.
func NewSignedAttestation(privateKey ed25519.PrivateKey, proofID, verifierID string, decision Decision, nonce uint64) (Attestation, error) {
	if len(privateKey) != ed25519.PrivateKeySize {
		return Attestation{}, errors.New("invalid Ed25519 private key")
	}
	if proofID == "" || verifierID == "" || nonce == 0 {
		return Attestation{}, errors.New("proof_id, verifier_id, and non-zero nonce are required")
	}
	if decision != DecisionAccept && decision != DecisionReject {
		return Attestation{}, errors.New("decision must be accept or reject")
	}
	a := Attestation{ProofID: proofID, VerifierID: verifierID, Decision: decision, Nonce: nonce}
	a.Signature = ed25519.Sign(privateKey, SignBytes(proofID, verifierID, decision, nonce))
	return a, nil
}

// ValidatePolicy checks verifier identity, key sizes, weights, and strict-majority quorum.
func ValidatePolicy(policy Policy) (uint64, error) {
	if len(policy.Verifiers) == 0 {
		return 0, errors.New("verifier set must not be empty")
	}
	var total uint64
	for id, verifier := range policy.Verifiers {
		if id == "" || verifier.ID != id {
			return 0, fmt.Errorf("verifier map key and ID must match and be non-empty")
		}
		if len(verifier.PublicKey) != ed25519.PublicKeySize {
			return 0, fmt.Errorf("verifier %q has an invalid Ed25519 public key", id)
		}
		if verifier.Weight == 0 {
			return 0, fmt.Errorf("verifier %q must have positive weight", id)
		}
		if math.MaxUint64-total < verifier.Weight {
			return 0, errors.New("total verifier weight overflows uint64")
		}
		total += verifier.Weight
	}
	if policy.Threshold == 0 || policy.Threshold > total || policy.Threshold <= total/2 {
		return 0, errors.New("threshold must be greater than half and no greater than total verifier weight")
	}
	return total, nil
}

// Evaluate verifies every vote and calculates a weighted result. Any malformed,
// unauthorized, duplicate, or invalidly signed vote fails closed.
func Evaluate(policy Policy, proofID string, votes []Attestation) (Result, error) {
	total, err := ValidatePolicy(policy)
	if err != nil {
		return Result{}, err
	}
	if proofID == "" {
		return Result{}, errors.New("proof_id must not be empty")
	}
	result := Result{Status: StatusPending, TotalWeight: total, Threshold: policy.Threshold}
	seen := make(map[string]struct{}, len(votes))
	for _, vote := range votes {
		if vote.ProofID != proofID {
			return Result{}, errors.New("attestation proof_id does not match evaluation target")
		}
		if vote.Nonce == 0 {
			return Result{}, errors.New("attestation nonce must be non-zero")
		}
		if vote.Decision != DecisionAccept && vote.Decision != DecisionReject {
			return Result{}, errors.New("attestation decision must be accept or reject")
		}
		verifier, ok := policy.Verifiers[vote.VerifierID]
		if !ok {
			return Result{}, fmt.Errorf("unauthorized verifier %q", vote.VerifierID)
		}
		if _, duplicate := seen[vote.VerifierID]; duplicate {
			return Result{}, fmt.Errorf("verifier %q has already attested this proof", vote.VerifierID)
		}
		if len(vote.Signature) != ed25519.SignatureSize ||
			!ed25519.Verify(verifier.PublicKey, SignBytes(vote.ProofID, vote.VerifierID, vote.Decision, vote.Nonce), vote.Signature) {
			return Result{}, fmt.Errorf("invalid signature from verifier %q", vote.VerifierID)
		}
		seen[vote.VerifierID] = struct{}{}
		switch vote.Decision {
		case DecisionAccept:
			result.AcceptWeight += verifier.Weight
		case DecisionReject:
			result.RejectWeight += verifier.Weight
		}
	}
	if result.AcceptWeight >= policy.Threshold {
		result.Status = StatusAccepted
	} else if result.RejectWeight >= policy.Threshold {
		result.Status = StatusRejected
	}
	return result, nil
}
