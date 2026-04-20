package types

import "errors"

type GenesisState struct {
	Params    Params           `json:"params"`
	Proposals []RightsProposal `json:"proposals"`
	NextID    uint64           `json:"next_id"`
}

type Params struct {
	// VotingPeriod is the duration of the voting window (in seconds).
	VotingPeriodSeconds int64 `json:"voting_period_seconds"`
	// MinDeposit is the minimum deposit required to activate a proposal (in udrp).
	MinDeposit uint64 `json:"min_deposit"`
}

func DefaultParams() Params {
	return Params{
		VotingPeriodSeconds: 172800, // 48 hours default
		MinDeposit:          10000000, // 10 DRP
	}
}

func DefaultGenesis() *GenesisState {
	return &GenesisState{
		Params:    DefaultParams(),
		Proposals: []RightsProposal{},
		NextID:    1,
	}
}

func (gs GenesisState) Validate() error {
	seen := make(map[uint64]bool)
	for _, p := range gs.Proposals {
		if seen[p.ID] {
			return errors.New("rights: duplicate proposal ID in genesis")
		}
		seen[p.ID] = true
		if p.Title == "" {
			return errors.New("rights: proposal title must not be empty")
		}
	}
	return nil
}
