package types

import "errors"

type GenesisState struct {
	Params      Params       `json:"params"`
	TrustStates []TrustState `json:"trust_states"`
}

type Params struct {
	// MaxActivityRefs caps the number of activity proof IDs stored per address.
	MaxActivityRefs uint64 `json:"max_activity_refs"`
}

func DefaultParams() Params  { return Params{MaxActivityRefs: 1000} }
func DefaultGenesis() *GenesisState {
	return &GenesisState{Params: DefaultParams(), TrustStates: []TrustState{}}
}
func (gs GenesisState) Validate() error {
	seen := make(map[string]bool)
	for _, ts := range gs.TrustStates {
		if seen[ts.Address] {
			return errors.New("trust: duplicate address in genesis")
		}
		seen[ts.Address] = true
	}
	return nil
}
