package app

import (
	"github.com/cosmos/cosmos-sdk/codec"
	"github.com/cosmos/cosmos-sdk/types/module"
	"github.com/cosmos/cosmos-sdk/x/auth/keeper"
	"github.com/cosmos/cosmos-sdk/x/bank/keeper"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/keeper"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// AddDeriModule adds the deri module to the module manager
// This function should be called from app.go to register the deri module
func AddDeriModule(
	app *DRPApp,
	cdc codec.Codec,
	accountKeeper types.AccountKeeper,
	bankKeeper types.BankKeeper,
	keys map[string]*storetypes.KVStoreKey,
	memKeys map[string]*storetypes.TransientStoreKey,
) error {
	// Create store keys for the deri module
	deriStoreKey := sdk.NewKVStoreKey(types.StoreKey)
	deriMemStoreKey := sdk.NewTransientStoreKey(types.MemStoreKey)

	keys[types.StoreKey] = deriStoreKey
	memKeys[types.MemStoreKey] = deriMemStoreKey

	// Create the keeper
	deriKeeper := keeper.NewKeeper(
		cdc,
		deriStoreKey,
		deriMemStoreKey,
		app.ParamsKeeper.Subspace(types.ModuleName),
		accountKeeper,
		bankKeeper,
		app.DistrKeeper,
		app.StakingKeeper,
	)

	// Create the module
	deriModule := deri.NewAppModule(cdc, deriKeeper, accountKeeper, bankKeeper)

	// Register the module
	app.mm.RegisterModules(deriModule)

	// Set the keeper in the app
	app.DeriKeeper = deriKeeper

	return nil
}

// RegisterDeriCodec registers the deri module codec
func RegisterDeriCodec(cdc *codec.LegacyAmino) {
	types.RegisterLegacyAminoCodec(cdc)
}

// RegisterDeriInterfaces registers the deri module interfaces
func RegisterDeriInterfaces(registry cdctypes.InterfaceRegistry) {
	types.RegisterInterfaces(registry)
}
