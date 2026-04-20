// Package types defines the core types for the x/poat (Proof-of-Activity) module.
//
// PoAT is designed to accept abstract activity proofs that verify meaningful
// contribution without revealing identity.  The on-chain record contains
// ONLY a commitment reference (content hash / CID) — raw activity data is
// NEVER stored here.
package types

const (
	// ModuleName is the canonical name used for store keys, router keys, etc.
	ModuleName = "poat"

	// StoreKey is the KV store key for the PoAT module.
	StoreKey = ModuleName

	// RouterKey is the message routing key.
	RouterKey = ModuleName

	// QuerierRoute is the querier route key.
	QuerierRoute = ModuleName
)

// Key prefixes for the PoAT KV store.
// Using explicit byte prefixes keeps the store layout stable and auditable.
var (
	// KeyPrefixProof is the prefix for activity proof records.
	KeyPrefixProof = []byte{0x01}

	// KeyPrefixProofBySubmitter is a secondary index (submitter → proof IDs).
	KeyPrefixProofBySubmitter = []byte{0x02}
)

// ActivityProofKey returns the store key for a given proof ID.
func ActivityProofKey(proofID string) []byte {
	return append(KeyPrefixProof, []byte(proofID)...)
}
