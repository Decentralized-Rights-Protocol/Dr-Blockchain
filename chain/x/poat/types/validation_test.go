package types

import (
	"encoding/base32"
	"strings"
	"testing"
)

func validTestCID() string {
	raw := []byte{0x01, 0x55, 0x12, 0x20}
	for i := 0; i < 32; i++ {
		raw = append(raw, byte(i+1))
	}
	return "b" + strings.ToLower(base32.StdEncoding.WithPadding(base32.NoPadding).EncodeToString(raw))
}

func TestValidateCID(t *testing.T) {
	if err := ValidateCID(validTestCID()); err != nil {
		t.Fatalf("valid CID rejected: %v", err)
	}
	for _, value := range []string{"", "QmNotCID", "bnot-base32!", "bafk", "z123"} {
		if err := ValidateCID(value); err == nil {
			t.Errorf("invalid CID %q accepted", value)
		}
	}
}

func TestValidateMetadataHash(t *testing.T) {
	if err := ValidateMetadataHash(strings.Repeat("a", 64)); err != nil {
		t.Fatal(err)
	}
	if err := ValidateMetadataHash("abc"); err == nil {
		t.Fatal("short hash accepted")
	}
	if err := ValidateMetadataHash(strings.Repeat("z", 64)); err == nil {
		t.Fatal("non-hex hash accepted")
	}
}

func TestBuildProofIDDeterministic(t *testing.T) {
	a := BuildProofID("submitter", validTestCID(), strings.Repeat("a", 64))
	b := BuildProofID("submitter", validTestCID(), strings.Repeat("a", 64))
	if a != b || len(a) != 64 {
		t.Fatal("proof ID must be deterministic SHA-256 hex")
	}
}
