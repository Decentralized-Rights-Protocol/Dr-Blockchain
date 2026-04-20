// Package keeper implements the DRP evidence module state management.
//
// Key design decisions:
//   1. Only EvidenceCommitment structs (CID + hashes + status) are stored.
//   2. No reference to IPFS node is held here; off-chain services use
//      the DRP_IPFS_API_URL env var to interact with IPFS.
//   3. The keeper exposes a clear "anchor / confirm / revoke" lifecycle.
package keeper

import (
	"encoding/json"
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/decentralized-rights-protocol/drp/chain/x/evidence/types"
)

// Keeper manages the DRP evidence module KV store.
type Keeper struct {
	cdc      codec.BinaryCodec
	storeKey storetypes.StoreKey
}

func NewKeeper(cdc codec.BinaryCodec, storeKey storetypes.StoreKey) Keeper {
	return Keeper{cdc: cdc, storeKey: storeKey}
}

// ── Commitment lifecycle ──────────────────────────────────────────────────────

// AnchorCommitment stores a new evidence commitment.
// Called by the msg server when MsgAnchorEvidence is processed.
func (k Keeper) AnchorCommitment(ctx sdk.Context, c types.EvidenceCommitment) {
	store := ctx.KVStore(k.storeKey)
	bz, err := json.Marshal(c)
	if err != nil {
		panic(fmt.Sprintf("evidence keeper: marshal error: %v", err))
	}
	store.Set(types.CommitmentKey(c.ID), bz)
}

// GetCommitment retrieves a commitment by ID.
func (k Keeper) GetCommitment(ctx sdk.Context, id string) (types.EvidenceCommitment, bool) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.CommitmentKey(id))
	if bz == nil {
		return types.EvidenceCommitment{}, false
	}
	var c types.EvidenceCommitment
	if err := json.Unmarshal(bz, &c); err != nil {
		panic(fmt.Sprintf("evidence keeper: unmarshal error: %v", err))
	}
	return c, true
}

// UpdateCommitmentStatus updates the status field of an existing commitment.
func (k Keeper) UpdateCommitmentStatus(ctx sdk.Context, id string, status types.CommitmentStatus) error {
	c, ok := k.GetCommitment(ctx, id)
	if !ok {
		return types.ErrCommitmentNotFound
	}
	c.Status = status
	k.AnchorCommitment(ctx, c)
	return nil
}

// GetAllCommitments returns all commitments for genesis export.
func (k Keeper) GetAllCommitments(ctx sdk.Context) []types.EvidenceCommitment {
	store := ctx.KVStore(k.storeKey)
	it := sdk.KVStorePrefixIterator(store, types.KeyPrefixCommitment)
	defer it.Close()
	var commitments []types.EvidenceCommitment
	for ; it.Valid(); it.Next() {
		var c types.EvidenceCommitment
		if err := json.Unmarshal(it.Value(), &c); err != nil {
			panic(fmt.Sprintf("evidence keeper: corrupt store: %v", err))
		}
		commitments = append(commitments, c)
	}
	return commitments
}

// ── Genesis ───────────────────────────────────────────────────────────────────

func (k Keeper) InitGenesis(ctx sdk.Context, gs types.GenesisState) {
	for _, c := range gs.Commitments {
		k.AnchorCommitment(ctx, c)
	}
}

func (k Keeper) ExportGenesis(ctx sdk.Context) *types.GenesisState {
	return &types.GenesisState{
		Params:      types.DefaultParams(),
		Commitments: k.GetAllCommitments(ctx),
	}
}
