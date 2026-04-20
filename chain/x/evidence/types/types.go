package types

import "time"

// CommitmentStatus represents the lifecycle state of an evidence commitment.
type CommitmentStatus int32

const (
	// CommitmentPending: anchored on-chain, awaiting off-chain verification.
	CommitmentPending CommitmentStatus = 0
	// CommitmentConfirmed: the CID has been verified as resolvable and structurally valid.
	CommitmentConfirmed CommitmentStatus = 1
	// CommitmentRevoked: the commitment has been revoked (content may be disputed).
	CommitmentRevoked CommitmentStatus = 2
)

// EvidenceCommitment is the on-chain record that anchors a piece of off-chain evidence.
//
// Privacy invariants:
//   - CID uniquely identifies the content in IPFS but reveals nothing about it.
//   - ContentHash allows verification of CID resolution without fetching content.
//   - MetadataHash allows verification of the metadata envelope without storing it.
//   - No fields contain personal information, free-text descriptions, or raw data.
//
// IPFS integration:
//   - CID must be a valid CIDv1 multihash string (base32 lowercase preferred).
//   - The full evidence bundle is pinned to the IPFS node configured via
//     DRP_IPFS_API_URL env var (see chain/.env.chain.example).
//   - The submission flow:
//       1. Client pins evidence to IPFS → gets CID.
//       2. Client computes SHA-256(evidence bytes) = ContentHash.
//       3. Client computes SHA-256(metadata_json) = MetadataHash.
//       4. Client calls MsgAnchorEvidence with (CID, ContentHash, MetadataHash).
//       5. Chain stores commitment; IPFS data remains off-chain.
type EvidenceCommitment struct {
	// ID is a deterministic identifier: sha256(submitter + cid + block_height).
	ID string `json:"id"`

	// Submitter is the bech32 address of the account anchoring the evidence.
	Submitter string `json:"submitter"`

	// CID is the IPFS content identifier of the evidence bundle.
	// Must be a valid CIDv1 string.  Example: bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi
	CID string `json:"cid"`

	// ContentHash is the hex-encoded SHA-256 of the raw evidence bytes.
	// Used to verify CID resolution without fetching the content.
	ContentHash string `json:"content_hash"`

	// MetadataHash is the hex-encoded SHA-256 of the JSON metadata envelope
	// that describes the evidence (type, format, version, etc.).
	MetadataHash string `json:"metadata_hash"`

	// EvidenceType categorises the evidence (e.g. "activity", "credential", "humanitarian").
	EvidenceType string `json:"evidence_type"`

	// Status is the current lifecycle state.
	Status CommitmentStatus `json:"status"`

	// SubmittedAt is the block time of first submission.
	SubmittedAt time.Time `json:"submitted_at"`

	// ConfirmedAt is set when the commitment is confirmed.
	ConfirmedAt *time.Time `json:"confirmed_at,omitempty"`
}
