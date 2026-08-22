package keeper

import (
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

func (k Keeper) InitializeModule(ctx sdk.Context, gs types.GenesisState) {
	if gs.MintAuthority != "" {
		mintAuthority, err := sdk.AccAddressFromBech32(gs.MintAuthority)
		if err == nil {
			k.SetMintAuthority(ctx, mintAuthority)
		}
	}
	k.SetEmissionLimits(ctx, gs.EmissionLimits)
	k.SetTotalSupply(ctx, gs.TotalSupply)
	for _, entry := range gs.Balances {
		addr, err := sdk.AccAddressFromBech32(entry.Address)
		if err == nil {
			k.SetBalance(ctx, addr, entry.Balance)
		}
	}
}

func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	var balances []types.BalanceEntry
	k.IterateBalances(ctx, func(addr sdk.AccAddress, balance sdk.Int) bool {
		balances = append(balances, types.NewBalanceEntry(addr.String(), balance))
		return false
	})
	totalSupply := k.GetTotalSupply(ctx)
	mintAuthority, _ := k.GetMintAuthority(ctx)
	emissionLimits := k.GetEmissionLimits(ctx)
	return types.NewGenesisState(balances, totalSupply, mintAuthority.String(), emissionLimits)
}

func (k Keeper) IterateBalances(ctx sdk.Context, handler func(sdk.AccAddress, sdk.Int) bool) {
	store := ctx.KVStore(k.storeKey)
	iterator := store.Iterator([]byte(types.BalancePrefix))
	defer iterator.Close()
	for ; iterator.Valid(); iterator.Next() {
		key := iterator.Key()
		address := string(key[len(types.BalancePrefix):])
		addr, err := sdk.AccAddressFromBech32(address)
		if err != nil {
			continue
		}
		var balance sdk.Int
		k.cdc.MustUnmarshalBinaryBare(iterator.Value(), &balance)
		if handler(addr, balance) {
			break
		}
	}
}