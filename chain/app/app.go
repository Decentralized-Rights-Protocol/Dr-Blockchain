// Package app wires the DRP sovereign L1 chain application.
//
// Design principles:
//   - Sovereign: no Cosmos Hub or shared security dependency.
//   - Modular: clean keeper boundaries, DRP modules isolated.
//   - Privacy-aware: only commitments/hashes stored on-chain.
//   - Future EVM compatibility: stable store key layout.
package app

import (
	"encoding/json"
	"io"

	dbm "github.com/cometbft/cometbft-db"
	abci "github.com/cometbft/cometbft/abci/types"
	cmtproto "github.com/cometbft/cometbft/proto/tendermint/types"
	cmtlog "github.com/cometbft/cometbft/libs/log"

	"github.com/cosmos/cosmos-sdk/baseapp"
	"github.com/cosmos/cosmos-sdk/codec"
	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	storetypes "github.com/cosmos/cosmos-sdk/store/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	"github.com/cosmos/cosmos-sdk/version"
	authkeeper "github.com/cosmos/cosmos-sdk/x/auth/keeper"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	vestingmodule "github.com/cosmos/cosmos-sdk/x/auth/vesting"
	authzkeeper "github.com/cosmos/cosmos-sdk/x/authz/keeper"
	authztypes "github.com/cosmos/cosmos-sdk/x/authz"
	authzmodule "github.com/cosmos/cosmos-sdk/x/authz/module"
	bankkeeper "github.com/cosmos/cosmos-sdk/x/bank/keeper"
	banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
	crisiskeeper "github.com/cosmos/cosmos-sdk/x/crisis/keeper"
	crisistypes "github.com/cosmos/cosmos-sdk/x/crisis/types"
	distrkeeper "github.com/cosmos/cosmos-sdk/x/distribution/keeper"
	distrtypes "github.com/cosmos/cosmos-sdk/x/distribution/types"
	feegrantkeeper "github.com/cosmos/cosmos-sdk/x/feegrant/keeper"
	feegranttypes "github.com/cosmos/cosmos-sdk/x/feegrant"
	feegrantmodule "github.com/cosmos/cosmos-sdk/x/feegrant/module"
	genutiltypes "github.com/cosmos/cosmos-sdk/x/genutil/types"
	govkeeper "github.com/cosmos/cosmos-sdk/x/gov/keeper"
	govtypes "github.com/cosmos/cosmos-sdk/x/gov/types"
	mintkeeper "github.com/cosmos/cosmos-sdk/x/mint/keeper"
	minttypes "github.com/cosmos/cosmos-sdk/x/mint/types"
	paramskeeper "github.com/cosmos/cosmos-sdk/x/params/keeper"
	paramstypes "github.com/cosmos/cosmos-sdk/x/params/types"
	slashingkeeper "github.com/cosmos/cosmos-sdk/x/slashing/keeper"
	slashingtypes "github.com/cosmos/cosmos-sdk/x/slashing/types"
	stakingkeeper "github.com/cosmos/cosmos-sdk/x/staking/keeper"
	stakingtypes "github.com/cosmos/cosmos-sdk/x/staking/types"
	upgradekeeper "github.com/cosmos/cosmos-sdk/x/upgrade/keeper"
	upgradetypes "github.com/cosmos/cosmos-sdk/x/upgrade/types"

	// Standard module constructors used in the module manager.
	"github.com/cosmos/cosmos-sdk/x/auth"
	"github.com/cosmos/cosmos-sdk/x/bank"
	"github.com/cosmos/cosmos-sdk/x/crisis"
	"github.com/cosmos/cosmos-sdk/x/distribution"
	"github.com/cosmos/cosmos-sdk/x/genutil"
	"github.com/cosmos/cosmos-sdk/x/gov"
	"github.com/cosmos/cosmos-sdk/x/mint"
	"github.com/cosmos/cosmos-sdk/x/params"
	"github.com/cosmos/cosmos-sdk/x/slashing"
	"github.com/cosmos/cosmos-sdk/x/staking"
	"github.com/cosmos/cosmos-sdk/x/upgrade"
	// DRP protocol modules temporarily disabled; will be re-enabled after SDK API updates.
)

const (
	// Name is the ABCI application name.
	Name = "drp"

	// BondDenom is the base staking/fee denomination.
	// This is a placeholder; DRP monetary policy will be finalised through governance.
	BondDenom = "udrp"
)

// maccPerms maps module account names to their permission sets.
var maccPerms = map[string][]string{
	authtypes.FeeCollectorName:     nil,
	distrtypes.ModuleName:          nil,
	minttypes.ModuleName:           {authtypes.Minter},
	stakingtypes.BondedPoolName:    {authtypes.Burner, authtypes.Staking},
	stakingtypes.NotBondedPoolName: {authtypes.Burner, authtypes.Staking},
	govtypes.ModuleName:            {authtypes.Burner},
}

// blockedAddresses returns the set of module account addresses that are
// blocked from receiving external transfers.
func blockedAddresses() map[string]bool {
	addrs := make(map[string]bool)
	for acc := range maccPerms {
		addrs[authtypes.NewModuleAddress(acc).String()] = true
	}
	// Distribution and governance receive funds through protocol mechanisms.
	delete(addrs, authtypes.NewModuleAddress(govtypes.ModuleName).String())
	delete(addrs, authtypes.NewModuleAddress(distrtypes.ModuleName).String())
	return addrs
}

// DRPApp is the main Cosmos SDK application for the Decentralized Rights Protocol.
type DRPApp struct {
	*baseapp.BaseApp

	cdc               codec.Codec
	legacyAmino       *codec.LegacyAmino
	interfaceRegistry codectypes.InterfaceRegistry

	keys  map[string]*storetypes.KVStoreKey
	tkeys map[string]*storetypes.TransientStoreKey

	// ── Cosmos SDK standard keepers ────────────────────────────────────────
	AccountKeeper  authkeeper.AccountKeeper
	BankKeeper     bankkeeper.BaseKeeper
	StakingKeeper  *stakingkeeper.Keeper
	MintKeeper     mintkeeper.Keeper
	DistrKeeper    distrkeeper.Keeper
	SlashingKeeper slashingkeeper.Keeper
	GovKeeper      *govkeeper.Keeper
	CrisisKeeper   crisiskeeper.Keeper
	UpgradeKeeper  *upgradekeeper.Keeper
	ParamsKeeper   paramskeeper.Keeper
	AuthzKeeper    authzkeeper.Keeper
	FeeGrantKeeper feegrantkeeper.Keeper

	// ── DRP protocol keepers ───────────────────────────────────────────────
	// (none)

	mm           *module.Manager
	configurator module.Configurator
}

// NewDRPApp constructs and returns a fully-wired DRPApp.
func NewDRPApp(
	logger cmtlog.Logger,
	db dbm.DB,
	traceStore io.Writer,
	loadLatest bool,
	appOpts servertypes.AppOptions,
	baseAppOptions ...func(*baseapp.BaseApp),
) *DRPApp {
	encodingConfig := MakeEncodingConfig()
	ModuleBasics.RegisterInterfaces(encodingConfig.InterfaceRegistry)

	bApp := baseapp.NewBaseApp(
		Name, logger, db,
		encodingConfig.TxConfig.TxDecoder(),
		baseAppOptions...,
	)
	bApp.SetCommitMultiStoreTracer(traceStore)
	bApp.SetVersion(version.Version)
	bApp.SetInterfaceRegistry(encodingConfig.InterfaceRegistry)

	// ── Store keys ──────────────────────────────────────────────────────────
	keys := sdk.NewKVStoreKeys(
		authtypes.StoreKey, banktypes.StoreKey, stakingtypes.StoreKey,
		minttypes.StoreKey, distrtypes.StoreKey, slashingtypes.StoreKey,
		govtypes.StoreKey, paramstypes.StoreKey, crisistypes.StoreKey,
		upgradetypes.StoreKey, feegranttypes.StoreKey, authztypes.ModuleName,
	)
	tkeys := sdk.NewTransientStoreKeys(paramstypes.TStoreKey)

	app := &DRPApp{
		BaseApp:           bApp,
		cdc:               encodingConfig.Marshaler,
		legacyAmino:       encodingConfig.Amino,
		interfaceRegistry: encodingConfig.InterfaceRegistry,
		keys:              keys,
		tkeys:             tkeys,
	}

	// ── Params keeper (legacy, for subspace support) ────────────────────────
	app.ParamsKeeper = initParamsKeeper(
		encodingConfig.Marshaler, encodingConfig.Amino,
		keys[paramstypes.StoreKey], tkeys[paramstypes.TStoreKey],
	)
	// Consensus params are managed by the consensus module in SDK v0.47+.

	govModAddr := authtypes.NewModuleAddress(govtypes.ModuleName).String()

	// ── Auth keeper ─────────────────────────────────────────────────────────
	app.AccountKeeper = authkeeper.NewAccountKeeper(
		encodingConfig.Marshaler, keys[authtypes.StoreKey],
		authtypes.ProtoBaseAccount, maccPerms,
		sdk.Bech32MainPrefix, govModAddr,
	)

	// ── Bank keeper ─────────────────────────────────────────────────────────
	app.BankKeeper = bankkeeper.NewBaseKeeper(
		encodingConfig.Marshaler, keys[banktypes.StoreKey],
		app.AccountKeeper, blockedAddresses(), govModAddr,
	)

	// ── Staking keeper ──────────────────────────────────────────────────────
	app.StakingKeeper = stakingkeeper.NewKeeper(
		encodingConfig.Marshaler, keys[stakingtypes.StoreKey],
		app.AccountKeeper, app.BankKeeper, govModAddr,
	)

	// ── Mint keeper ─────────────────────────────────────────────────────────
	app.MintKeeper = mintkeeper.NewKeeper(
		encodingConfig.Marshaler, keys[minttypes.StoreKey],
		app.StakingKeeper, app.AccountKeeper, app.BankKeeper,
		authtypes.FeeCollectorName, govModAddr,
	)

	// ── Distribution keeper ─────────────────────────────────────────────────
	app.DistrKeeper = distrkeeper.NewKeeper(
		encodingConfig.Marshaler, keys[distrtypes.StoreKey],
		app.AccountKeeper, app.BankKeeper, app.StakingKeeper,
		authtypes.FeeCollectorName, govModAddr,
	)

	// ── Slashing keeper ─────────────────────────────────────────────────────
	app.SlashingKeeper = slashingkeeper.NewKeeper(
		encodingConfig.Marshaler, encodingConfig.Amino,
		keys[slashingtypes.StoreKey], app.StakingKeeper, govModAddr,
	)

	// ── Crisis keeper ───────────────────────────────────────────────────────
	app.CrisisKeeper = *crisiskeeper.NewKeeper(
		encodingConfig.Marshaler, keys[crisistypes.StoreKey],
		0, app.BankKeeper, authtypes.FeeCollectorName, govModAddr,
	)

	// ── Upgrade keeper ──────────────────────────────────────────────────────
	app.UpgradeKeeper = upgradekeeper.NewKeeper(
		map[int64]bool{}, keys[upgradetypes.StoreKey],
		encodingConfig.Marshaler, DefaultNodeHome, app.BaseApp, govModAddr,
	)

	// ── Authz & FeeGrant keepers ────────────────────────────────────────────
	app.AuthzKeeper = authzkeeper.NewKeeper(
		keys[authztypes.ModuleName], encodingConfig.Marshaler,
		app.MsgServiceRouter(), app.AccountKeeper,
	)
	app.FeeGrantKeeper = feegrantkeeper.NewKeeper(
		encodingConfig.Marshaler, keys[feegranttypes.StoreKey], app.AccountKeeper,
	)

	// ── Gov keeper ──────────────────────────────────────────────────────────
	// Standard cosmos gov v1. x/rights extends governance with DRP-specific proposals.
	app.GovKeeper = govkeeper.NewKeeper(
		encodingConfig.Marshaler, keys[govtypes.StoreKey],
		app.AccountKeeper, app.BankKeeper, app.StakingKeeper,
		app.MsgServiceRouter(), govtypes.DefaultConfig(), govModAddr,
	)

	// Register staking hooks (distr + slashing must hook into staking).
	app.StakingKeeper.SetHooks(
		stakingtypes.NewMultiStakingHooks(
			app.DistrKeeper.Hooks(),
			app.SlashingKeeper.Hooks(),
		),
	)

	// ── DRP keepers (none while modules are disabled) ──────────────────────

	// ── Module manager ──────────────────────────────────────────────────────
	app.mm = module.NewManager(
		genutil.NewAppModule(app.AccountKeeper, app.StakingKeeper, app.BaseApp.DeliverTx, encodingConfig.TxConfig),
		auth.NewAppModule(encodingConfig.Marshaler, app.AccountKeeper, nil, app.GetSubspace(authtypes.ModuleName)),
		vestingmodule.NewAppModule(app.AccountKeeper, app.BankKeeper),
		bank.NewAppModule(encodingConfig.Marshaler, app.BankKeeper, app.AccountKeeper, app.GetSubspace(banktypes.ModuleName)),
		crisis.NewAppModule(&app.CrisisKeeper, false, app.GetSubspace(crisistypes.ModuleName)),
		feegrantmodule.NewAppModule(encodingConfig.Marshaler, app.AccountKeeper, app.BankKeeper, app.FeeGrantKeeper, app.interfaceRegistry),
		authzmodule.NewAppModule(encodingConfig.Marshaler, app.AuthzKeeper, app.AccountKeeper, app.BankKeeper, app.interfaceRegistry),
		gov.NewAppModule(encodingConfig.Marshaler, app.GovKeeper, app.AccountKeeper, app.BankKeeper, app.GetSubspace(govtypes.ModuleName)),
		mint.NewAppModule(encodingConfig.Marshaler, app.MintKeeper, app.AccountKeeper, nil, app.GetSubspace(minttypes.ModuleName)),
		slashing.NewAppModule(encodingConfig.Marshaler, app.SlashingKeeper, app.AccountKeeper, app.BankKeeper, app.StakingKeeper, app.GetSubspace(slashingtypes.ModuleName)),
		distribution.NewAppModule(encodingConfig.Marshaler, app.DistrKeeper, app.AccountKeeper, app.BankKeeper, app.StakingKeeper, app.GetSubspace(distrtypes.ModuleName)),
		staking.NewAppModule(encodingConfig.Marshaler, app.StakingKeeper, app.AccountKeeper, app.BankKeeper, app.GetSubspace(stakingtypes.ModuleName)),
		upgrade.NewAppModule(app.UpgradeKeeper),
		params.NewAppModule(app.ParamsKeeper),
	)

	app.mm.SetOrderBeginBlockers(
		upgradetypes.ModuleName, minttypes.ModuleName, distrtypes.ModuleName,
		slashingtypes.ModuleName, stakingtypes.ModuleName, authtypes.ModuleName,
		banktypes.ModuleName, govtypes.ModuleName, crisistypes.ModuleName,
		genutiltypes.ModuleName, authztypes.ModuleName, feegranttypes.ModuleName,
		paramstypes.ModuleName, "vesting",
	)

	app.mm.SetOrderEndBlockers(
		crisistypes.ModuleName, govtypes.ModuleName, stakingtypes.ModuleName,
		upgradetypes.ModuleName, minttypes.ModuleName, distrtypes.ModuleName,
		slashingtypes.ModuleName, authtypes.ModuleName, banktypes.ModuleName,
		authztypes.ModuleName, feegranttypes.ModuleName, paramstypes.ModuleName,
		genutiltypes.ModuleName, "vesting",
	)

	app.mm.SetOrderInitGenesis(
		authtypes.ModuleName, banktypes.ModuleName, distrtypes.ModuleName,
		stakingtypes.ModuleName, slashingtypes.ModuleName, govtypes.ModuleName,
		minttypes.ModuleName, crisistypes.ModuleName, genutiltypes.ModuleName,
		authztypes.ModuleName, feegranttypes.ModuleName, upgradetypes.ModuleName,
		paramstypes.ModuleName, "vesting",
	)

	app.mm.RegisterInvariants(&app.CrisisKeeper)
	app.configurator = module.NewConfigurator(app.cdc, app.MsgServiceRouter(), app.GRPCQueryRouter())
	app.mm.RegisterServices(app.configurator)

	app.SetInitChainer(app.InitChainer)
	app.SetBeginBlocker(app.BeginBlocker)
	app.SetEndBlocker(app.EndBlocker)

	app.MountKVStores(keys)
	app.MountTransientStores(tkeys)

	if loadLatest {
		if err := app.LoadLatestVersion(); err != nil {
			panic(err)
		}
	}
	return app
}

// ── ABCI handlers ─────────────────────────────────────────────────────────────

func (app *DRPApp) InitChainer(ctx sdk.Context, req abci.RequestInitChain) abci.ResponseInitChain {
	var genesisState map[string]json.RawMessage
	if err := json.Unmarshal(req.AppStateBytes, &genesisState); err != nil {
		panic(err)
	}
	app.UpgradeKeeper.SetModuleVersionMap(ctx, app.mm.GetVersionMap())
	return app.mm.InitGenesis(ctx, app.cdc, genesisState)
}

func (app *DRPApp) BeginBlocker(ctx sdk.Context, req abci.RequestBeginBlock) abci.ResponseBeginBlock {
	return app.mm.BeginBlock(ctx, req)
}

func (app *DRPApp) EndBlocker(ctx sdk.Context, req abci.RequestEndBlock) abci.ResponseEndBlock {
	return app.mm.EndBlock(ctx, req)
}

// ── Exported helpers ──────────────────────────────────────────────────────────

func (app *DRPApp) GetSubspace(moduleName string) paramstypes.Subspace {
	subspace, _ := app.ParamsKeeper.GetSubspace(moduleName)
	return subspace
}

func (app *DRPApp) DefaultGenesis() map[string]json.RawMessage {
	return ModuleBasics.DefaultGenesis(app.cdc)
}

func (app *DRPApp) ExportAppStateAndValidators(
	forZeroHeight bool,
	jailAllowedAddrs []string,
	modulesToExport []string,
) (servertypes.ExportedApp, error) {
	ctx := app.NewContext(true, cmtproto.Header{Height: app.LastBlockHeight()})

	height := app.LastBlockHeight() + 1
	if forZeroHeight {
		height = 0
		app.prepForZeroHeightGenesis(ctx, jailAllowedAddrs)
	}

	genState := app.mm.ExportGenesisForModules(ctx, app.cdc, modulesToExport)
	appState, err := json.MarshalIndent(genState, "", "  ")
	if err != nil {
		return servertypes.ExportedApp{}, err
	}

	validators, err := staking.WriteValidators(ctx, app.StakingKeeper)
	if err != nil {
		return servertypes.ExportedApp{}, err
	}

	return servertypes.ExportedApp{
		AppState:        appState,
		Validators:      validators,
		Height:          height,
		ConsensusParams: app.BaseApp.GetConsensusParams(ctx),
	}, nil
}

func (app *DRPApp) prepForZeroHeightGenesis(ctx sdk.Context, _ []string) {
	app.SlashingKeeper.IterateValidatorSigningInfos(ctx,
		func(addr sdk.ConsAddress, info slashingtypes.ValidatorSigningInfo) bool {
			info.StartHeight = 0
			app.SlashingKeeper.SetValidatorSigningInfo(ctx, addr, info)
			return false
		},
	)
}

// ── Params keeper setup ────────────────────────────────────────────────────────

func initParamsKeeper(
	appCodec codec.BinaryCodec,
	legacyAmino *codec.LegacyAmino,
	key, tkey storetypes.StoreKey,
) paramskeeper.Keeper {
	pk := paramskeeper.NewKeeper(appCodec, legacyAmino, key, tkey)
	pk.Subspace(authtypes.ModuleName)
	pk.Subspace(banktypes.ModuleName)
	pk.Subspace(stakingtypes.ModuleName)
	pk.Subspace(minttypes.ModuleName)
	pk.Subspace(distrtypes.ModuleName)
	pk.Subspace(slashingtypes.ModuleName)
	pk.Subspace(govtypes.ModuleName)
	pk.Subspace(crisistypes.ModuleName)
	pk.Subspace(baseapp.Paramspace)
	return pk
}
