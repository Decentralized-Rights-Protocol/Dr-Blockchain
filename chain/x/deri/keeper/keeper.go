package keeper

import (
	"fmt"

	"github.com/cosmos/cosmos-sdk/codec"
	sdk "github.com/cosmos/cosmos-sdk/types"
	paramtypes "github.com/cosmos/cosmos-sdk/x/params/types"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// Keeper defines the keeper for the deri module
type Keeper struct {
	cdc           codec.BinaryCodec
	storeKey     sdk.StoreKey
	memStoreKey  sdk.StoreKey
	paramSpace   paramtypes.Subspace
	authKeeper   types.AuthKeeper
	bankKeeper   types.BankKeeper
	distrKeeper  types.DistrKeeper
	stakingKeeper types.StakingKeeper
}

// NewKeeper creates a new Keeper instance
func NewKeeper(
	cdc codec.BinaryCodec,
	storeKey sdk.StoreKey,
	memStoreKey sdk.StoreKey,
	paramSpace paramtypes.Subspace,
	authKeeper types.AuthKeeper,
	bankKeeper types.BankKeeper,
	distrKeeper types.DistrKeeper,
	stakingKeeper types.StakingKeeper,
) *Keeper {
	// Ensure the paramSpace has the correct key table
	if !paramSpace.HasKeyTable() {
		paramSpace = paramSpace.WithKeyTable(types.ParamKeyTable())
	}

	return &Keeper{
		cdc:           cdc,
		storeKey:     storeKey,
		memStoreKey:  memStoreKey,
		paramSpace:   paramSpace,
		authKeeper:   authKeeper,
		bankKeeper:   bankKeeper,
		distrKeeper:  distrKeeper,
		stakingKeeper: stakingKeeper,
	}
}

// Logger returns a module-specific logger
func (k Keeper) Logger(ctx sdk.Context) sdk.Logger {
	return ctx.Logger().With("module", fmt.Sprintf("x/%s", types.ModuleName))
}

// GetParams returns the current parameters from the store
func (k Keeper) GetParams(ctx sdk.Context) (params types.Params, err error) {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.GetParamsKey())
	if bz == nil {
		return types.DefaultParams(), nil
	}

	if err := k.cdc.Unmarshal(bz, &params); err != nil {
		return params, err
	}
	return params, nil
}

// SetParams sets the parameters in the store
func (k Keeper) SetParams(ctx sdk.Context, params types.Params) error {
	store := ctx.KVStore(k.storeKey)
	bz, err := k.cdc.Marshal(&params)
	if err != nil {
		return err
	}
	store.Set(types.GetParamsKey(), bz)
	return nil
}

// GetBalance returns the $DeRi balance of an account
func (k Keeper) GetBalance(ctx sdk.Context, address sdk.AccAddress) sdk.Int {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.GetBalanceKey(address))
	if bz == nil {
		return sdk.ZeroInt()
	}

	var balance sdk.Int
	if err := balance.Unmarshal(bz); err != nil {
		k.Logger(ctx).Error("failed to unmarshal balance", "error", err)
		return sdk.ZeroInt()
	}
	return balance
}

// SetBalance sets the $DeRi balance of an account
func (k Keeper) SetBalance(ctx sdk.Context, address sdk.AccAddress, amount sdk.Int) error {
	store := ctx.KVStore(k.storeKey)
	bz, err := amount.Marshal()
	if err != nil {
		return err
	}
	store.Set(types.GetBalanceKey(address), bz)
	return nil
}

// AddBalance adds to the $DeRi balance of an account
func (k Keeper) AddBalance(ctx sdk.Context, address sdk.AccAddress, amount sdk.Int) error {
	balance := k.GetBalance(ctx, address)
	newBalance := balance.Add(amount)
	return k.SetBalance(ctx, address, newBalance)
}

// SubtractBalance subtracts from the $DeRi balance of an account
func (k Keeper) SubtractBalance(ctx sdk.Context, address sdk.AccAddress, amount sdk.Int) error {
	balance := k.GetBalance(ctx, address)
	if balance.LT(amount) {
		return fmt.Errorf("insufficient balance: %s < %s", balance, amount)
	}
	newBalance := balance.Sub(amount)
	return k.SetBalance(ctx, address, newBalance)
}

// GetTotalSupply returns the total supply of $DeRi
func (k Keeper) GetTotalSupply(ctx sdk.Context) sdk.Int {
	store := ctx.KVStore(k.storeKey)
	bz := store.Get(types.GetTotalSupplyKey())
	if bz == nil {
		return sdk.ZeroInt()
	}

	var totalSupply sdk.Int
	if err := totalSupply.Unmarshal(bz); err != nil {
		k.Logger(ctx).Error("failed to unmarshal total supply", "error", err)
		return sdk.ZeroInt()
	}
	return totalSupply
}

// SetTotalSupply sets the total supply of $DeRi
func (k Keeper) SetTotalSupply(ctx sdk.Context, amount sdk.Int) error {
	store := ctx.KVStore(k.storeKey)
	bz, err := amount.Marshal()
	if err != nil {
		return err
	}
	store.Set(types.GetTotalSupplyKey(), bz)
	return nil
}

// Mint mints new $DeRi tokens to an account
// This is a controlled operation that respects emission limits
func (k Keeper) Mint(ctx sdk.Context, to sdk.AccAddress, amount sdk.Int, reason string) error {
	params, err := k.GetParams(ctx)
	if err != nil {
		return err
	}

	// Check emission limits
	if amount.GT(sdk.NewInt(params.MaxPerBlock)) {
		return fmt.Errorf("mint amount exceeds per-block limit: %s > %d", amount, params.MaxPerBlock)
	}

	// Add to account balance
	if err := k.AddBalance(ctx, to, amount); err != nil {
		return err
	}

	// Update total supply
	totalSupply := k.GetTotalSupply(ctx)
	newTotalSupply := totalSupply.Add(amount)
	if err := k.SetTotalSupply(ctx, newTotalSupply); err != nil {
		return err
	}

	// Record mint history
	height := ctx.BlockHeight()
	mintRecord := types.MintRecord{
		Height:   height,
		To:       to.String(),
		Amount:   amount.String(),
		Reason:   reason,
		Timestamp: ctx.BlockTime().Unix(),
	}
	k.setMintRecord(ctx, height, mintRecord)

	k.Logger(ctx).Info("minted tokens", "to", to, "amount", amount, "reason", reason)
	return nil
}

// Burn burns $DeRi tokens from an account
func (k Keeper) Burn(ctx sdk.Context, from sdk.AccAddress, amount sdk.Int, reason string) error {
	// Subtract from account balance
	if err := k.SubtractBalance(ctx, from, amount); err != nil {
		return err
	}

	// Update total supply
	totalSupply := k.GetTotalSupply(ctx)
	newTotalSupply := totalSupply.Sub(amount)
	if err := k.SetTotalSupply(ctx, newTotalSupply); err != nil {
		return err
	}

	// Record burn history
	height := ctx.BlockHeight()
	burnRecord := types.BurnRecord{
		Height:   height,
		From:     from.String(),
		Amount:   amount.String(),
		Reason:   reason,
		Timestamp: ctx.BlockTime().Unix(),
	}
	k.setBurnRecord(ctx, height, burnRecord)

	k.Logger(ctx).Info("burned tokens", "from", from, "amount", amount, "reason", reason)
	return nil
}

// Transfer transfers $DeRi tokens from one account to another
func (k Keeper) Transfer(ctx sdk.Context, from, to sdk.AccAddress, amount sdk.Int) error {
	// Subtract from sender
	if err := k.SubtractBalance(ctx, from, amount); err != nil {
		return err
	}

	// Add to recipient
	if err := k.AddBalance(ctx, to, amount); err != nil {
		return err
	}

	k.Logger(ctx).Info("transferred tokens", "from", from, "to", to, "amount", amount)
	return nil
}

// setMintRecord stores a mint record
func (k Keeper) setMintRecord(ctx sdk.Context, height int64, record types.MintRecord) {
	store := ctx.KVStore(k.storeKey)
	bz, err := k.cdc.Marshal(&record)
	if err != nil {
		k.Logger(ctx).Error("failed to marshal mint record", "error", err)
		return
	}
	store.Set(types.GetMintHistoryKey(height), bz)
}

// setBurnRecord stores a burn record
func (k Keeper) setBurnRecord(ctx sdk.Context, height int64, record types.BurnRecord) {
	store := ctx.KVStore(k.storeKey)
	bz, err := k.cdc.Marshal(&record)
	if err != nil {
		k.Logger(ctx).Error("failed to marshal burn record", "error", err)
		return
	}
	store.Set(types.GetBurnHistoryKey(height), bz)
}

// CalculateReward calculates a reward using the deterministic formula
func (k Keeper) CalculateReward(
	ctx sdk.Context,
	baseReward, activityScore, verificationConf, reputationMult, networkFactor int64,
) (int64, error) {
	// Use the deterministic calculation from types
	reward := types.CalculateReward(baseReward, activityScore, verificationConf, reputationMult, networkFactor)
	
	// Validate the reward
	if err := types.ValidateReward(reward); err != nil {
		return 0, err
	}

	// Check against emission limits
	params, err := k.GetParams(ctx)
	if err != nil {
		return 0, err
	}

	if reward > params.MaxPerActivity {
		return params.MaxPerActivity, nil
	}

	return reward, nil
}
