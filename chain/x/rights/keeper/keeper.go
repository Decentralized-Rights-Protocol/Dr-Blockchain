// Package keeper implements the rights module state management.
package keeper

import (
	"encoding/binary"
	"encoding/json"
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/decentralized-rights-protocol/drp/chain/x/rights/types"
)

var nextIDKey = []byte("nextProposalID")

type Keeper struct {
	cdc      codec.BinaryCodec
	storeKey storetypes.StoreKey
}

func NewKeeper(cdc codec.BinaryCodec, storeKey storetypes.StoreKey) Keeper {
	return Keeper{cdc: cdc, storeKey: storeKey}
}

func (k Keeper) SetProposal(ctx sdk.Context, p types.RightsProposal) {
	store := ctx.KVStore(k.storeKey)
	bz, err := json.Marshal(p)
	if err != nil {
		panic(fmt.Sprintf("rights keeper: marshal error: %v", err))
	}
	store.Set(types.ProposalKey(p.ID), bz)
}

func (k Keeper) GetProposal(ctx sdk.Context, id uint64) (types.RightsProposal, bool) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.ProposalKey(id))
	if bz == nil {
		return types.RightsProposal{}, false
	}
	var p types.RightsProposal
	if err := json.Unmarshal(bz, &p); err != nil {
		panic(fmt.Sprintf("rights keeper: unmarshal error: %v", err))
	}
	return p, true
}

func (k Keeper) NextProposalID(ctx sdk.Context) uint64 {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(nextIDKey)
	if bz == nil {
		return 1
	}
	return binary.BigEndian.Uint64(bz)
}

func (k Keeper) SetNextProposalID(ctx sdk.Context, id uint64) {
	store := ctx.KVStore(k.storeKey)
	bz := make([]byte, 8)
	binary.BigEndian.PutUint64(bz, id)
	store.Set(nextIDKey, bz)
}

func (k Keeper) GetAllProposals(ctx sdk.Context) []types.RightsProposal {
	store := ctx.KVStore(k.storeKey)
	it := sdk.KVStorePrefixIterator(store, types.KeyPrefixProposal)
	defer it.Close()
	var proposals []types.RightsProposal
	for ; it.Valid(); it.Next() {
		var p types.RightsProposal
		if err := json.Unmarshal(it.Value(), &p); err != nil {
			panic(fmt.Sprintf("rights keeper: corrupt store: %v", err))
		}
		proposals = append(proposals, p)
	}
	return proposals
}

func (k Keeper) InitGenesis(ctx sdk.Context, gs types.GenesisState) {
	k.SetNextProposalID(ctx, gs.NextID)
	for _, p := range gs.Proposals {
		k.SetProposal(ctx, p)
	}
}

func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	return &types.GenesisState{
		Params:    types.DefaultParams(),
		Proposals: k.GetAllProposals(ctx),
		NextID:    k.NextProposalID(ctx),
	}
}
