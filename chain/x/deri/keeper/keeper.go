package keeper

import (
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	paramtypes "github.com/cosmos/cosmos-sdk/x/params/types"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

type Keeper struct {
	cdc         codec.BinaryCodec
	storeKey    storetypes.StoreKey
	paramSpace  paramtypes.Subspace
	authKeeper  types.AccountKeeper
	bankKeeper  types.BankKeeper
}

func NewKeeper(
	cdc codec.BinaryCodec,
	storeKey storetypes.StoreKey,
	paramSpace paramtypes.Subspace,
	authKeeper types.AccountKeeper,
	bankKeeper types.BankKeeper,
) *Keeper {
	if !paramSpace.HasKeyTable() {
		paramSpace = paramSpace.WithKeyTable(types.ParamKeyTable())
	}
	return &Keeper{
		cdc:        cdc,
		storeKey:   storeKey,
		paramSpace: paramSpace,
		authKeeper: authKeeper,
		bankKeeper: bankKeeper,
	}
}

func (k Keeper) GetMintAuthority(ctx sdk.Context) (sdk.AccAddress, error) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.MintAuthorityKey)
	if len(bz) == 0 {
		return sdk.AccAddressFromBech32(types.ModuleName), nil
	}
	var authority string
	k.cdc.MustUnmarshalBinaryBare(bz, &authority)
	return sdk.AccAddressFromBech32(authority)
}

func (k Keeper) SetMintAuthority(ctx sdk.Context, authority sdk.AccAddress) {
	store := ctx.KVStore(k.storeKey)
	store.Set(types.MintAuthorityKey, k.cdc.MustMarshalBinaryBare(authority.String()))
}

func (k Keeper) GetEmissionLimits(ctx sdk.Context) types.EmissionLimits {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.EmissionLimitsKey)
	var limits types.EmissionLimits
	if len(bz) == 0 {
		return types.DefaultEmissionLimits()
	}
	k.cdc.MustUnmarshalBinaryBare(bz, &limits)
	return limits
}

func (k Keeper) SetEmissionLimits(ctx sdk.Context, limits types.EmissionLimits) {
	store := ctx.KVStore(k.storeKey)
	store.Set(types.EmissionLimitsKey, k.cdc.MustMarshalBinaryBare(&limits))
}

func (k Keeper) GetBalance(ctx sdk.Context, addr sdk.AccAddress) sdk.Int {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.BalanceKey(addr))
	if len(bz) == 0 {
		return sdk.ZeroInt()
	}
	var balance sdk.Int
	k.cdc.MustUnmarshalBinaryBare(bz, &balance)
	return balance
}

func (k Keeper) SetBalance(ctx sdk.Context, addr sdk.AccAddress, amount sdk.Int) {
	store := ctx.KVStore(k.storeKey)
	store.Set(types.BalanceKey(addr), k.cdc.MustMarshalBinaryBare(&amount))
}

func (k Keeper) AddBalance(ctx sdk.Context, addr sdk.AccAddress, amount sdk.Int) sdk.Int {
	balance := k.GetBalance(ctx, addr)
	newBalance := balance.Add(amount)
	k.SetBalance(ctx, addr, newBalance)
	return newBalance
}

func (k Keeper) SubtractBalance(ctx sdk.Context, addr sdk.AccAddress, amount sdk.Int) (sdk.Int, error) {
	balance := k.GetBalance(ctx, addr)
	if balance.LT(amount) {
		return sdk.ZeroInt(), fmt.Errorf("insufficient balance")
	}
	newBalance := balance.Sub(amount)
	k.SetBalance(ctx, addr, newBalance)
	return newBalance, nil
}

func (k Keeper) GetTotalSupply(ctx sdk.Context) sdk.Int {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.TotalSupplyKey)
	if len(bz) == 0 {
		return sdk.ZeroInt()
	}
	var supply sdk.Int
	k.cdc.MustUnmarshalBinaryBare(bz, &supply)
	return supply
}

func (k Keeper) SetTotalSupply(ctx sdk.Context, amount sdk.Int) {
	store := ctx.KVStore(k.storeKey)
	store.Set(types.TotalSupplyKey, k.cdc.MustMarshalBinaryBare(&amount))
}