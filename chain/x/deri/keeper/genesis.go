package keeper

import (
	"fmt"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/decentralized-rights-protocol/drp/chain/x/deri/types"
)

func (k Keeper) InitGenesis(ctx sdk.Context, state *types.GenesisState) {
	if state == nil {
		panic("nil deri genesis")
	}
	if err := state.Validate(); err != nil {
		panic(err)
	}
	if err := k.SetParams(ctx, state.Params); err != nil {
		panic(err)
	}
	supply, _ := sdk.NewIntFromString(state.TotalSupply)
	if err := k.SetTotalSupply(ctx, supply); err != nil {
		panic(err)
	}
	for _, balance := range state.Balances {
		address, _ := sdk.AccAddressFromBech32(balance.Address)
		amount, _ := sdk.NewIntFromString(balance.Amount)
		if err := k.SetBalance(ctx, address, amount); err != nil {
			panic(err)
		}
	}
	for _, record := range state.MintHistory {
		k.setMintRecord(ctx, record.Height, record)
	}
	for _, record := range state.BurnHistory {
		k.setBurnRecord(ctx, record.Height, record)
	}
}

func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	params, err := k.GetParams(ctx)
	if err != nil {
		panic(err)
	}
	state := types.NewGenesisState(params, []types.BalanceGenesis{}, k.GetTotalSupply(ctx).String())
	k.IterateBalances(ctx, func(address sdk.AccAddress, amount sdk.Int) bool {
		state.Balances = append(state.Balances, types.BalanceGenesis{Address: address.String(), Amount: amount.String()})
		return false
	})
	k.IterateMintHistory(ctx, func(record types.MintRecord) bool {
		state.MintHistory = append(state.MintHistory, record)
		return false
	})
	k.IterateBurnHistory(ctx, func(record types.BurnRecord) bool {
		state.BurnHistory = append(state.BurnHistory, record)
		return false
	})
	return state
}

func (k Keeper) IterateBalances(ctx sdk.Context, handler func(sdk.AccAddress, sdk.Int) bool) {
	iter := sdk.KVStorePrefixIterator(ctx.KVStore(k.storeKey), types.KeyPrefixBalance)
	defer iter.Close()
	for ; iter.Valid(); iter.Next() {
		address := sdk.AccAddress(iter.Key()[len(types.KeyPrefixBalance):])
		var amount sdk.Int
		if err := amount.Unmarshal(iter.Value()); err != nil {
			panic(fmt.Errorf("invalid stored balance: %w", err))
		}
		if handler(address, amount) {
			break
		}
	}
}

func (k Keeper) IterateMintHistory(ctx sdk.Context, handler func(types.MintRecord) bool) {
	iter := sdk.KVStorePrefixIterator(ctx.KVStore(k.storeKey), types.KeyPrefixMintHistory)
	defer iter.Close()
	for ; iter.Valid(); iter.Next() {
		var record types.MintRecord
		if err := k.cdc.Unmarshal(iter.Value(), &record); err != nil {
			panic(fmt.Errorf("invalid stored mint record: %w", err))
		}
		if handler(record) {
			break
		}
	}
}

func (k Keeper) IterateBurnHistory(ctx sdk.Context, handler func(types.BurnRecord) bool) {
	iter := sdk.KVStorePrefixIterator(ctx.KVStore(k.storeKey), types.KeyPrefixBurnHistory)
	defer iter.Close()
	for ; iter.Valid(); iter.Next() {
		var record types.BurnRecord
		if err := k.cdc.Unmarshal(iter.Value(), &record); err != nil {
			panic(fmt.Errorf("invalid stored burn record: %w", err))
		}
		if handler(record) {
			break
		}
	}
}
