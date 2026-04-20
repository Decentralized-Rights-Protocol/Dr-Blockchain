// Package keeper implements the PoST module state management.
package keeper

import (
	"encoding/json"
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/decentralized-rights-protocol/drp/chain/x/post/types"
)

// Keeper manages the PoST module KV store.
type Keeper struct {
	cdc      codec.BinaryCodec
	storeKey storetypes.StoreKey
}

func NewKeeper(cdc codec.BinaryCodec, storeKey storetypes.StoreKey) Keeper {
	return Keeper{cdc: cdc, storeKey: storeKey}
}

func (k Keeper) SetStatusRecord(ctx sdk.Context, record types.StatusRecord) {
	store := ctx.KVStore(k.storeKey)
	bz, err := json.Marshal(record)
	if err != nil {
		panic(fmt.Sprintf("post keeper: marshal error: %v", err))
	}
	store.Set(types.StatusRecordKey(record.ID), bz)
}

func (k Keeper) GetStatusRecord(ctx sdk.Context, id string) (types.StatusRecord, bool) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.StatusRecordKey(id))
	if bz == nil {
		return types.StatusRecord{}, false
	}
	var r types.StatusRecord
	if err := json.Unmarshal(bz, &r); err != nil {
		panic(fmt.Sprintf("post keeper: unmarshal error: %v", err))
	}
	return r, true
}

func (k Keeper) GetAllRecords(ctx sdk.Context) []types.StatusRecord {
	store := ctx.KVStore(k.storeKey)
	it := sdk.KVStorePrefixIterator(store, types.KeyPrefixStatus)
	defer it.Close()
	var records []types.StatusRecord
	for ; it.Valid(); it.Next() {
		var r types.StatusRecord
		if err := json.Unmarshal(it.Value(), &r); err != nil {
			panic(fmt.Sprintf("post keeper: corrupt store: %v", err))
		}
		records = append(records, r)
	}
	return records
}

func (k Keeper) InitGenesis(ctx sdk.Context, gs types.GenesisState) {
	for _, r := range gs.Records {
		k.SetStatusRecord(ctx, r)
	}
}

func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	return &types.GenesisState{
		Params:  types.DefaultParams(),
		Records: k.GetAllRecords(ctx),
	}
}
