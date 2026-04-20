// Package keeper implements the PoAT module state management.
//
// The keeper only ever stores commitment metadata (CID, hash, status).
// Raw evidence data is stored off-chain in IPFS and referenced by CID.
package keeper

import (
	"encoding/json"
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/decentralized-rights-protocol/drp/chain/x/poat/types"
)

// Keeper manages the PoAT module KV store.
type Keeper struct {
	cdc      codec.BinaryCodec
	storeKey storetypes.StoreKey
}

// NewKeeper creates a new PoAT keeper.
func NewKeeper(cdc codec.BinaryCodec, storeKey storetypes.StoreKey) Keeper {
	return Keeper{cdc: cdc, storeKey: storeKey}
}

// ── Activity Proof CRUD ───────────────────────────────────────────────────────

// SetActivityProof stores an activity proof record.
func (k Keeper) SetActivityProof(ctx sdk.Context, proof types.ActivityProof) {
	store := ctx.KVStore(k.storeKey)
	key := types.ActivityProofKey(proof.ID)
	bz, err := json.Marshal(proof)
	if err != nil {
		panic(fmt.Sprintf("poat keeper: failed to marshal proof %s: %v", proof.ID, err))
	}
	store.Set(key, bz)
}

// GetActivityProof retrieves an activity proof by ID.
// Returns (proof, true) if found, (zero, false) otherwise.
func (k Keeper) GetActivityProof(ctx sdk.Context, proofID string) (types.ActivityProof, bool) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.ActivityProofKey(proofID))
	if bz == nil {
		return types.ActivityProof{}, false
	}
	var proof types.ActivityProof
	if err := json.Unmarshal(bz, &proof); err != nil {
		panic(fmt.Sprintf("poat keeper: failed to unmarshal proof %s: %v", proofID, err))
	}
	return proof, true
}

// DeleteActivityProof removes an activity proof record.
func (k Keeper) DeleteActivityProof(ctx sdk.Context, proofID string) {
	store := ctx.KVStore(k.storeKey)
	store.Delete(types.ActivityProofKey(proofID))
}

// GetAllProofs returns all activity proofs for genesis export.
func (k Keeper) GetAllProofs(ctx sdk.Context) []types.ActivityProof {
	store := ctx.KVStore(k.storeKey)
	it := sdk.KVStorePrefixIterator(store, types.KeyPrefixProof)
	defer it.Close()

	var proofs []types.ActivityProof
	for ; it.Valid(); it.Next() {
		var proof types.ActivityProof
		if err := json.Unmarshal(it.Value(), &proof); err != nil {
			panic(fmt.Sprintf("poat keeper: corrupt store entry: %v", err))
		}
		proofs = append(proofs, proof)
	}
	return proofs
}

// ── Genesis support ───────────────────────────────────────────────────────────

// InitGenesis loads the module state from a genesis state.
func (k Keeper) InitGenesis(ctx sdk.Context, gs types.GenesisState) {
	for _, proof := range gs.Proofs {
		k.SetActivityProof(ctx, proof)
	}
}

// ExportGenesis exports the module state for genesis serialisation.
func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	return &types.GenesisState{
		Params: types.DefaultParams(),
		Proofs: k.GetAllProofs(ctx),
	}
}
