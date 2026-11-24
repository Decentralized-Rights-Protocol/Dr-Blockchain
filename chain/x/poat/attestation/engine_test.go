package attestation

import (
	"crypto/ed25519"
	"crypto/rand"
	"testing"
)

func testPolicy(t *testing.T) (Policy, map[string]ed25519.PrivateKey) {
	t.Helper()
	policy := Policy{Verifiers: make(map[string]Verifier), Threshold: 3}
	private := make(map[string]ed25519.PrivateKey)
	for _, id := range []string{"elder-a", "elder-b", "elder-c", "elder-d"} {
		pub, key, err := ed25519.GenerateKey(rand.Reader)
		if err != nil { t.Fatal(err) }
		private[id] = key
		policy.Verifiers[id] = Verifier{ID: id, PublicKey: pub, Weight: 1}
	}
	return policy, private
}

func vote(t *testing.T, private map[string]ed25519.PrivateKey, id, proof string, decision Decision) Attestation {
	t.Helper()
	v, err := NewSignedAttestation(private[id], proof, id, decision, 1)
	if err != nil { t.Fatal(err) }
	return v
}

func TestEvaluateAcceptsAtThreshold(t *testing.T) {
	p, keys := testPolicy(t)
	votes := []Attestation{
		vote(t, keys, "elder-a", "proof-1", DecisionAccept),
		vote(t, keys, "elder-b", "proof-1", DecisionAccept),
		vote(t, keys, "elder-c", "proof-1", DecisionAccept),
	}
	got, err := Evaluate(p, "proof-1", votes)
	if err != nil { t.Fatal(err) }
	if got.Status != StatusAccepted || got.AcceptWeight != 3 || got.RejectWeight != 0 {
		t.Fatalf("unexpected result: %+v", got)
	}
}

func TestEvaluateRejectsAtThreshold(t *testing.T) {
	p, keys := testPolicy(t)
	votes := []Attestation{
		vote(t, keys, "elder-a", "proof-1", DecisionReject),
		vote(t, keys, "elder-b", "proof-1", DecisionReject),
		vote(t, keys, "elder-c", "proof-1", DecisionReject),
	}
	got, err := Evaluate(p, "proof-1", votes)
	if err != nil { t.Fatal(err) }
	if got.Status != StatusRejected { t.Fatalf("expected rejected, got %+v", got) }
}

func TestEvaluateRemainsPendingBelowThreshold(t *testing.T) {
	p, keys := testPolicy(t)
	votes := []Attestation{
		vote(t, keys, "elder-a", "proof-1", DecisionAccept),
		vote(t, keys, "elder-b", "proof-1", DecisionAccept),
		vote(t, keys, "elder-c", "proof-1", DecisionReject),
	}
	got, err := Evaluate(p, "proof-1", votes)
	if err != nil { t.Fatal(err) }
	if got.Status != StatusPending { t.Fatalf("expected pending, got %+v", got) }
}

func TestEvaluateFailsClosedForDuplicateVerifier(t *testing.T) {
	p, keys := testPolicy(t)
	v := vote(t, keys, "elder-a", "proof-1", DecisionAccept)
	if _, err := Evaluate(p, "proof-1", []Attestation{v, v}); err == nil {
		t.Fatal("expected duplicate verifier error")
	}
}

func TestEvaluateFailsClosedForUnauthorizedVerifier(t *testing.T) {
	p, keys := testPolicy(t)
	v := vote(t, keys, "elder-a", "proof-1", DecisionAccept)
	v.VerifierID = "unknown"
	if _, err := Evaluate(p, "proof-1", []Attestation{v}); err == nil {
		t.Fatal("expected unauthorized verifier error")
	}
}

func TestEvaluateFailsClosedForInvalidSignature(t *testing.T) {
	p, keys := testPolicy(t)
	v := vote(t, keys, "elder-a", "proof-1", DecisionAccept)
	v.Signature[0] ^= 0xff
	if _, err := Evaluate(p, "proof-1", []Attestation{v}); err == nil {
		t.Fatal("expected invalid signature error")
	}
}

func TestEvaluateRejectsWrongProofID(t *testing.T) {
	p, keys := testPolicy(t)
	v := vote(t, keys, "elder-a", "proof-other", DecisionAccept)
	if _, err := Evaluate(p, "proof-1", []Attestation{v}); err == nil {
		t.Fatal("expected proof ID mismatch")
	}
}

func TestValidatePolicyRequiresStrictMajority(t *testing.T) {
	p, _ := testPolicy(t)
	p.Threshold = 2
	if _, err := ValidatePolicy(p); err == nil {
		t.Fatal("expected strict-majority threshold error")
	}
}
