package types

import (
	"fmt"

	"github.com/cosmos/cosmos-sdk/types"
)

const (
	ModuleName   = "deri"
	StoreKey     = ModuleName
	RouterKey    = ModuleName
	QuerierRoute = ModuleName
	MemStoreKey  = "mem_deri"
)

type EmissionLimits struct {
	MaxPerBlock    types.Int `json:"max_per_block" yaml:"max_per_block"`
	MaxPerEpoch    types.Int `json:"max_per_epoch" yaml:"max_per_epoch"`
	MaxPerActivity types.Int `json:"max_per_activity" yaml:"max_per_activity"`
	MaxPerIdentity types.Int `json:"max_per_identity" yaml:"max_per_identity"`
}

func NewEmissionLimits() EmissionLimits {
	return EmissionLimits{
		MaxPerBlock:    types.NewInt(1000000),
		MaxPerEpoch:    types.NewInt(100000000),
		MaxPerActivity: types.NewInt(10000),
		MaxPerIdentity: types.NewInt(1000000),
	}
}

type GenesisState struct {
	Balances      []BalanceEntry `json:"balances" yaml:"balances"`
	TotalSupply   types.Int        `json:"total_supply" yaml:"total_supply"`
	MintAuthority string         `json:"mint_authority" yaml:"mint_authority"`
	EmissionLimits EmissionLimits `json:"emission_limits" yaml:"emission_limits"`
}

type BalanceEntry struct {
	Address string  `json:"address" yaml:"address"`
	Balance types.Int `json:"balance" yaml:"balance"`
}