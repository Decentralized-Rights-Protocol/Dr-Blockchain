package types

import "time"

// TrustState holds the accumulated trust information for a single address.
//
// Design note: Trust is earned, not bought.  There are no transfers.
// The score field is a placeholder; final computation will be governance-defined.
type TrustState struct {
	// Address is the bech32 participant address.
	Address string `json:"address"`

	// TrustScore is a non-negative integer representing cumulative trust.
	// Scale TBD by governance; initially 0–10000.
	TrustScore uint64 `json:"trust_score"`

	// ActivityRefs is the list of PoAT proof IDs that contributed to this state.
	ActivityRefs []string `json:"activity_refs"`

	// StatusRef is the most recent PoST status record ID for this address.
	StatusRef string `json:"status_ref,omitempty"`

	// LastUpdated is the block time of the most recent state change.
	LastUpdated time.Time `json:"last_updated"`
}
