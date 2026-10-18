package types

import (
	"fmt"
	"math/big"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func NewGenesisState(params Params, balances []BalanceGenesis, totalSupply string) *GenesisState {
	return &GenesisState{Params: params, Balances: balances, TotalSupply: totalSupply, MintHistory: []MintRecord{}, BurnHistory: []BurnRecord{}}
}

func DefaultGenesisState() *GenesisState {
	return NewGenesisState(DefaultParams(), []BalanceGenesis{}, "0")
}

// Validate checks balances by decoded address and reconciles supply before any writes.
func (gs GenesisState) Validate() error {
	if err := gs.Params.Validate(); err != nil {
		return fmt.Errorf("invalid params: %w", err)
	}
	seen := make(map[string]bool)
	sum := new(big.Int)
	for _, balance := range gs.Balances {
		address, err := sdk.AccAddressFromBech32(balance.Address)
		if err != nil {
			return fmt.Errorf("invalid balance address %q: %w", balance.Address, err)
		}
		key := string(address)
		if seen[key] {
			return fmt.Errorf("duplicate balance address: %s", balance.Address)
		}
		seen[key] = true
		amount, ok := sdk.NewIntFromString(balance.Amount)
		if !ok || amount.IsNegative() {
			return fmt.Errorf("invalid nonnegative balance for %s: %s", balance.Address, balance.Amount)
		}
		sum.Add(sum, amount.BigInt())
	}
	supply, ok := sdk.NewIntFromString(gs.TotalSupply)
	if !ok || supply.IsNegative() {
		return fmt.Errorf("invalid nonnegative total supply: %s", gs.TotalSupply)
	}
	if sum.Cmp(supply.BigInt()) != 0 {
		return fmt.Errorf("total supply %s does not equal balances %s", supply, sum)
	}
	return nil
}
