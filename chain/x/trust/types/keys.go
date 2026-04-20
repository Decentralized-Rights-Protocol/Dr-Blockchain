// Package types defines x/trust (Trust State) module types.
//
// The trust module tracks contribution-linked trust state for each participant.
// Trust scores evolve through verified activity (PoAT) and status (PoST) records.
// The scoring formula is intentionally not hardcoded — it will be finalized via
// governance once the protocol matures.
package types

const (
	ModuleName   = "trust"
	StoreKey     = ModuleName
	RouterKey    = ModuleName
	QuerierRoute = ModuleName
)

var (
	KeyPrefixTrustState = []byte{0x01}
	KeyPrefixTrustIndex = []byte{0x02}
)

func TrustStateKey(address string) []byte {
	return append(KeyPrefixTrustState, []byte(address)...)
}
