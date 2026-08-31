package keeper

import (
	"fmt"

	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// GenesisState defines the genesis state for the deri module
type GenesisState struct {
	Params      types.Params         `json:"params" yaml:"params"`
	Balances    []BalanceGenesis     `json:"balances" yaml:"balances"`
	TotalSupply string               `json:"total_supply" yaml:"total_supply"`
	MintHistory []types.MintRecord   `json:"mint_history" yaml:"mint_history"`
	BurnHistory []types.BurnRecord   `json:"burn_history" yaml:"burn_history"`
}

// BalanceGenesis defines a balance entry in genesis
type BalanceGenesis struct {
	Address string `json:"address" yaml:"address"`
	Amount  string `json:"amount" yaml:"amount"`
}

// NewGenesisState creates a new GenesisState instance
func NewGenesisState(params types.Params, balances []BalanceGenesis, totalSupply string) *GenesisState {
	return &GenesisState{
		Params:      params,
		Balances:    balances,
		TotalSupply: totalSupply,
		MintHistory: []types.MintRecord{},
		BurnHistory: []types.BurnRecord{},
	}
}

// DefaultGenesisState returns the default genesis state
func DefaultGenesisState() *GenesisState {
	return NewGenesisState(
		types.DefaultParams(),
		[]BalanceGenesis{},
		"0",
	)
}

// Validate performs basic validation on genesis data
func (gs GenesisState) Validate() error {
	if err := gs.Params.Validate(); err != nil {
		return fmt.Errorf("invalid params: %w", err)
	}

	for _, balance := range gs.Balances {
		if balance.Address == "" {
			return fmt.Errorf("balance address cannot be empty")
		}
		if balance.Amount == "" {
			return fmt.Errorf("balance amount cannot be empty for address %s", balance.Address)
		}
		if _, ok := sdk.NewIntFromString(balance.Amount); !ok {
			return fmt.Errorf("invalid balance amount: %s", balance.Amount)
		}
	}

	if gs.TotalSupply == "" {
		return fmt.Errorf("total supply cannot be empty")
	}
	if _, ok := sdk.NewIntFromString(gs.TotalSupply); !ok {
		return fmt.Errorf("invalid total supply: %s", gs.TotalSupply)
	}

	return nil
}

// InitGenesis initializes the module from genesis state
func (k Keeper) InitGenesis(ctx sdk.Context, genState *GenesisState) {
	// Set params
	if err := k.SetParams(ctx, genState.Params); err != nil {
		panic(fmt.Errorf("failed to set params: %w", err))
	}

	// Set total supply
	totalSupply, ok := sdk.NewIntFromString(genState.TotalSupply)
	if !ok {
		panic(fmt.Errorf("invalid total supply in genesis: %s", genState.TotalSupply))
	}
	if err := k.SetTotalSupply(ctx, totalSupply); err != nil {
		panic(fmt.Errorf("failed to set total supply: %w", err))
	}

	// Set balances
	for _, balance := range genState.Balances {
		address, err := sdk.AccAddressFromBech32(balance.Address)
		if err != nil {
			panic(fmt.Errorf("invalid address in genesis: %s: %w", balance.Address, err))
		}

		amount, ok := sdk.NewIntFromString(balance.Amount)
		if !ok {
			panic(fmt.Errorf("invalid amount in genesis for %s: %s", balance.Address, balance.Amount))
		}

		if err := k.SetBalance(ctx, address, amount); err != nil {
			panic(fmt.Errorf("failed to set balance for %s: %w", balance.Address, err))
		}
	}

	// Restore mint history
	for _, record := range genState.MintHistory {
		k.setMintRecord(ctx, record.Height, record)
	}

	// Restore burn history
	for _, record := range genState.BurnHistory {
		k.setBurnRecord(ctx, record.Height, record)
	}
}

// ExportGenesis exports the module state to genesis format
func (k Keeper) ExportGenesis(ctx sdk.Context) *GenesisState {
	params, err := k.GetParams(ctx)
	if err != nil {
		panic(fmt.Errorf("failed to get params: %w", err))
	}

	totalSupply := k.GetTotalSupply(ctx)

	// Get all balances
	var balances []BalanceGenesis
	k.IterateBalances(ctx, func(address sdk.AccAddress, amount sdk.Int) bool {
		balances = append(balances, BalanceGenesis{
			Address: address.String(),
			Amount:  amount.String(),
		})
		return false
	})

	// Get mint history
	var mintHistory []types.MintRecord
	k.IterateMintHistory(ctx, func(record types.MintRecord) bool {
		mintHistory = append(mintHistory, record)
		return false
	})

	// Get burn history
	var burnHistory []types.BurnRecord
	k.IterateBurnHistory(ctx, func(record types.BurnRecord) bool {
		burnHistory = append(burnHistory, record)
		return false
	})

	return &GenesisState{
		Params:      params,
		Balances:    balances,
		TotalSupply: totalSupply.String(),
		MintHistory: mintHistory,
		BurnHistory: burnHistory,
	}
}

// IterateBalances iterates over all balances
func (k Keeper) IterateBalances(ctx sdk.Context, handler func(sdk.AccAddress, sdk.Int) bool) {
	store := ctx.KVStore(k.storeKey)
	iter := sdk.KVStorePrefixIterator(store, types.KeyPrefixBalance)
	defer iter.Close()

	for ; iter.Valid(); iter.Next() {
		address := sdk.AccAddress(iter.Key()[1:])
		var amount sdk.Int
		if err := amount.Unmarshal(iter.Value()); err != nil {
			k.Logger(ctx).Error("failed to unmarshal balance", "key", iter.Key(), "error", err)
			continue
		}
		if handler(address, amount) {
			break
		}
	}
}

// IterateMintHistory iterates over all mint history records
func (k Keeper) IterateMintHistory(ctx sdk.Context, handler func(types.MintRecord) bool) {
	store := ctx.KVStore(k.storeKey)
	iter := sdk.KVStorePrefixIterator(store, types.KeyPrefixMintHistory)
	defer iter.Close()

	for ; iter.Valid(); iter.Next() {
		var record types.MintRecord
		if err := k.cdc.Unmarshal(iter.Value(), &record); err != nil {
			k.Logger(ctx).Error("failed to unmarshal mint record", "key", iter.Key(), "error", err)
			continue
		}
		if handler(record) {
			break
		}
	}
}

// IterateBurnHistory iterates over all burn history records
func (k Keeper) IterateBurnHistory(ctx sdk.Context, handler func(types.BurnRecord) bool) {
	store := ctx.KVStore(k.storeKey)
	iter := sdk.KVStorePrefixIterator(store, types.KeyPrefixBurnHistory)
	defer iter.Close()

	for ; iter.Valid(); iter.Next() {
		var record types.BurnRecord
		if err := k.cdc.Unmarshal(iter.Value(), &record); err != nil {
			k.Logger(ctx).Error("failed to unmarshal burn record", "key", iter.Key(), "error", err)
			continue
		}
		if handler(record) {
			break
		}
	}
}
