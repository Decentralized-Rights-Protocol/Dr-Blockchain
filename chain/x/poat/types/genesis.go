package types

// GenesisState defines the PoAT module genesis state.
// At genesis there are no pre-existing activity proofs.
type GenesisState struct {
	Params Params          `json:"params"`
	Proofs []ActivityProof `json:"proofs"`
}

// Params holds the governance-settable parameters for the PoAT module.
type Params struct {
	// MaxProofsPerBlock caps proof submissions per block to prevent spam.
	MaxProofsPerBlock uint64 `json:"max_proofs_per_block"`
	// AllowedProofTypes is the set of accepted proof type strings.
	// An empty slice means all types are accepted (open during early development).
	AllowedProofTypes []string `json:"allowed_proof_types"`
}

// DefaultParams returns safe defaults for the PoAT module.
func DefaultParams() Params {
	return Params{
		MaxProofsPerBlock: 100,
		AllowedProofTypes: []string{},
	}
}

// DefaultGenesis returns the default genesis state for PoAT.
func DefaultGenesis() *GenesisState {
	return &GenesisState{
		Params: DefaultParams(),
		Proofs: []ActivityProof{},
	}
}

// Validate performs basic validation of the genesis state.
func (gs GenesisState) Validate() error {
	// Proof IDs must be unique.
	seen := make(map[string]bool)
	for _, p := range gs.Proofs {
		if seen[p.ID] {
			return ErrDuplicateProofID
		}
		seen[p.ID] = true
	}
	return nil
}
