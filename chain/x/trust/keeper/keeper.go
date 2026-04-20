// Package keeper implements the trust module state management.
package keeper

import (
	"encoding/json"
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/decentralized-rights-protocol/drp/chain/x/trust/types"
)

type Keeper struct {
	cdc      codec.BinaryCodec
	storeKey storetypes.StoreKey
}

func NewKeeper(cdc codec.BinaryCodec, storeKey storetypes.StoreKey) Keeper {
	return Keeper{cdc: cdc, storeKey: storeKey}
}

func (k Keeper) SetTrustState(ctx sdk.Context, ts types.TrustState) {
	store := ctx.KVStore(k.storeKey)
	bz, err := json.Marshal(ts)
	if err != nil {
		panic(fmt.Sprintf("trust keeper: marshal error: %v", err))
	}
	store.Set(types.TrustStateKey(ts.Address), bz)
}

func (k Keeper) GetTrustState(ctx sdk.Context, address string) (types.TrustState, bool) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.TrustStateKey(address))
	if bz == nil {
		return types.TrustState{}, false
	}
	var ts types.TrustState
	if err := json.Unmarshal(bz, &ts); err != nil {
		panic(fmt.Sprintf("trust keeper: unmarshal error: %v", err))
	}
	return ts, true
}

func (k Keeper) GetAllTrustStates(ctx sdk.Context) []types.TrustState {
	store := ctx.KVStore(k.storeKey)
	it := sdk.KVStorePrefixIterator(store, types.KeyPrefixTrustState)
	defer it.Close()
	var states []types.TrustState
	for ; it.Valid(); it.Next() {
		var ts types.TrustState
		if err := json.Unmarshal(it.Value(), &ts); err != nil {
			panic(fmt.Sprintf("trust keeper: corrupt store: %v", err))
		}
		states = append(states, ts)
	}
	return states
}

func (k Keeper) InitGenesis(ctx sdk.Context, gs types.GenesisState) {
	for _, ts := range gs.TrustStates {
		k.SetTrustState(ctx, ts)
	}
}

func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	return &types.GenesisState{
		Params:      types.DefaultParams(),
		TrustStates: k.GetAllTrustStates(ctx),
	}
}
