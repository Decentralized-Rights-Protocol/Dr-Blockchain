// Package types defines the x/post (Proof-of-Status) module types.
//
// PoST represents the trust/status evolution of a participant.
// Status records are non-transferable by design — they cannot be traded
// or assigned to another address; they must be earned through verifiable
// activity.
package types

const (
	ModuleName   = "post"
	StoreKey     = ModuleName
	RouterKey    = ModuleName
	QuerierRoute = ModuleName
)

var (
	KeyPrefixStatus          = []byte{0x01}
	KeyPrefixStatusBySubject = []byte{0x02}
)

func StatusRecordKey(id string) []byte {
	return append(KeyPrefixStatus, []byte(id)...)
}
