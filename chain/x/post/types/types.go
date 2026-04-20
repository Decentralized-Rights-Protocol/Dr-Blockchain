package types

import "time"

// StatusLevel describes the trust/status tier of a participant.
// Levels are intentionally non-numeric to resist speculation treatment.
type StatusLevel string

const (
	StatusLevelUnknown   StatusLevel = "unknown"
	StatusLevelObserver  StatusLevel = "observer"
	StatusLevelContributor StatusLevel = "contributor"
	StatusLevelVerified  StatusLevel = "verified"
	StatusLevelTrusted   StatusLevel = "trusted"
)

// StatusRecord is the on-chain representation of a participant's trust status.
//
// Design constraints:
//   - Non-transferable: Subject address is immutable after issuance.
//   - Privacy-preserving: BasisCID points to off-chain evidence; no PII on-chain.
//   - Revocable: Issuer or governance can revoke with a reason.
type StatusRecord struct {
	// ID is a deterministic identifier: sha256(subject + issuer + issued_at).
	ID string `json:"id"`

	// Subject is the bech32 address whose status this record describes.
	Subject string `json:"subject"`

	// StatusLevel is the current trust tier of the subject.
	StatusLevel StatusLevel `json:"status_level"`

	// BasisCID is an IPFS CID pointing to the off-chain evidence that
	// justified this status assignment.  May be empty for genesis records.
	BasisCID string `json:"basis_cid"`

	// Issuer is the bech32 address of the entity that issued this record.
	// Typically a governance module address or a trusted verifier.
	Issuer string `json:"issuer"`

	// IssuedAt is the block time of initial issuance.
	IssuedAt time.Time `json:"issued_at"`

	// ExpiresAt is an optional expiry time. Zero means no expiry.
	ExpiresAt *time.Time `json:"expires_at,omitempty"`

	// Revoked indicates whether this record has been revoked.
	Revoked bool `json:"revoked"`

	// RevocationReason is a human-readable note stored when Revoked=true.
	RevocationReason string `json:"revocation_reason,omitempty"`
}
