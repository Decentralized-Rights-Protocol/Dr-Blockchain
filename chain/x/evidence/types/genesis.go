package types

import "errors"

type GenesisState struct {
	Params      Params               `json:"params"`
	Commitments []EvidenceCommitment `json:"commitments"`
}

// Params holds governance-tunable parameters for the evidence module.
type Params struct {
	// MaxCommitmentsPerBlock caps submissions per block.
	MaxCommitmentsPerBlock uint64 `json:"max_commitments_per_block"`
	// AllowedEvidenceTypes: empty = all types allowed.
	AllowedEvidenceTypes []string `json:"allowed_evidence_types"`
	// IPFSGatewayURL is the default public IPFS gateway for CID resolution.
	// This is a convenience param and NOT used for on-chain verification.
	// Override with DRP_IPFS_GATEWAY_URL env var in off-chain services.
	IPFSGatewayURL string `json:"ipfs_gateway_url"`
}

func DefaultParams() Params {
	return Params{
		MaxCommitmentsPerBlock: 50,
		AllowedEvidenceTypes:   []string{},
		IPFSGatewayURL:         "https://ipfs.io/ipfs/",
	}
}

func DefaultGenesis() *GenesisState {
	return &GenesisState{Params: DefaultParams(), Commitments: []EvidenceCommitment{}}
}

func (gs GenesisState) Validate() error {
	seen := make(map[string]bool)
	for _, c := range gs.Commitments {
		if seen[c.ID] {
			return errors.New("drpevidence: duplicate commitment ID in genesis")
		}
		seen[c.ID] = true
		if c.CID == "" {
			return errors.New("drpevidence: commitment CID must not be empty")
		}
	}
	return nil
}
