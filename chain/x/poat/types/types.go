package types

import "time"

// ProofStatus represents the lifecycle state of an activity proof.
type ProofStatus int32

const (
	// ProofStatusPending: submitted but not yet verified.
	ProofStatusPending ProofStatus = 0
	// ProofStatusAccepted: verified and accepted as valid contribution evidence.
	ProofStatusAccepted ProofStatus = 1
	// ProofStatusRejected: failed verification.
	ProofStatusRejected ProofStatus = 2
	// ProofStatusRevoked: previously accepted but later invalidated.
	ProofStatusRevoked ProofStatus = 3
)

// ActivityProof is the on-chain record for a submitted activity proof.
//
// Design note: This record contains NO personal data.  The CommitmentCID
// points to off-chain evidence (stored in IPFS) that is referenced only by
// its content hash.  Verifiers check the CID structure and metadata hash;
// the content itself is never on-chain.
type ActivityProof struct {
	// ID is a deterministic identifier: sha256(submitter + commitment_cid + nonce).
	ID string `json:"id"`

	// Submitter is the bech32 address of the account that submitted the proof.
	Submitter string `json:"submitter"`

	// CommitmentCID is an IPFS content identifier pointing to the off-chain
	// evidence bundle.  Must be a valid CIDv1 multihash string.
	CommitmentCID string `json:"commitment_cid"`

	// ProofType identifies the category of activity (e.g. "education",
	// "community", "humanitarian").  Used for routing to the correct verifier.
	ProofType string `json:"proof_type"`

	// MetadataHash is a SHA-256 hash of the structured metadata JSON that
	// accompanied this proof at submission time.  Provides a tamper-evident
	// anchor without storing the metadata itself.
	MetadataHash string `json:"metadata_hash"`

	// Status is the current lifecycle state of this proof.
	Status ProofStatus `json:"status"`

	// SubmittedAt is the block time when the proof was first anchored.
	SubmittedAt time.Time `json:"submitted_at"`

	// UpdatedAt is the block time of the most recent status change.
	UpdatedAt time.Time `json:"updated_at"`
}
