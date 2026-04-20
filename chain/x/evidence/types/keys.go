// Package types defines x/evidence module types.
//
// The DRP evidence module implements a privacy-aware evidence anchoring layer.
//
// Architecture:
//   Raw evidence data lives in IPFS (or compatible content-addressed storage).
//   The chain stores ONLY:
//     - The content identifier (CID) that addresses the evidence in IPFS.
//     - A content hash (SHA-256) for tamper detection.
//     - A metadata hash (SHA-256 of a JSON metadata envelope).
//     - Lifecycle state (pending / confirmed / revoked).
//
//   This design means:
//     - Personal data never reaches the chain.
//     - Evidence can be referenced and verified without exposure.
//     - The module is IPFS-vendor-neutral: any CIDv1-compatible store works.
package types

const (
	ModuleName   = "drpevidence"
	StoreKey     = ModuleName
	RouterKey    = ModuleName
	QuerierRoute = ModuleName
)

var (
	KeyPrefixCommitment          = []byte{0x01}
	KeyPrefixCommitmentBySubject = []byte{0x02}
	KeyPrefixCommitmentByCID     = []byte{0x03}
)

func CommitmentKey(id string) []byte {
	return append(KeyPrefixCommitment, []byte(id)...)
}
