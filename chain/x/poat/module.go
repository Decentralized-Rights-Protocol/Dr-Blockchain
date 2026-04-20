// Package poat implements the Proof-of-Activity (PoAT) Cosmos SDK module.
//
// PoAT is designed to:
//   - Accept abstract activity proofs identified by an IPFS CID commitment.
//   - Verify meaningful contribution without exposing identity.
//   - Route proof types to appropriate off-chain or future on-chain verifiers.
//
// On-chain state: only commitment metadata (CID, type, hash, status).
// Raw evidence data: stored in IPFS, referenced by content hash.
package poat

import (
	"encoding/json"

	"github.com/spf13/cobra"
	abci "github.com/cometbft/cometbft/abci/types"

	"github.com/cosmos/cosmos-sdk/codec"
	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	simtypes "github.com/cosmos/cosmos-sdk/types/simulation"

	"github.com/decentralized-rights-protocol/drp/chain/x/poat/keeper"
	"github.com/decentralized-rights-protocol/drp/chain/x/poat/types"
)

var (
	_ module.AppModuleBasic = AppModuleBasic{}
	_ module.AppModule      = AppModule{}
)

// AppModuleBasic defines the basic application module for PoAT.
type AppModuleBasic struct{}

func (AppModuleBasic) Name() string { return types.ModuleName }

func (AppModuleBasic) RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	types.RegisterLegacyAminoCodec(cdc)
}

func (AppModuleBasic) RegisterInterfaces(registry codectypes.InterfaceRegistry) {
	types.RegisterInterfaces(registry)
}

func (AppModuleBasic) DefaultGenesis(cdc codec.JSONCodec) json.RawMessage {
	return marshalGenesis(cdc, types.DefaultGenesis())
}

func (AppModuleBasic) ValidateGenesis(cdc codec.JSONCodec, _ interface{}, bz json.RawMessage) error {
	var gs types.GenesisState
	if err := json.Unmarshal(bz, &gs); err != nil {
		return err
	}
	return gs.Validate()
}

func (AppModuleBasic) RegisterGRPCGatewayRoutes(_ interface{}, _ interface{}) {}
func (AppModuleBasic) GetTxCmd() *cobra.Command                               { return nil }
func (AppModuleBasic) GetQueryCmd() *cobra.Command                            { return nil }

// ── AppModule ─────────────────────────────────────────────────────────────────

// AppModule is the full application module for PoAT.
type AppModule struct {
	AppModuleBasic
	cdc    codec.Codec
	keeper keeper.Keeper
}

// NewAppModule creates a new PoAT AppModule.
func NewAppModule(cdc codec.Codec, k keeper.Keeper) AppModule {
	return AppModule{cdc: cdc, keeper: k}
}

func (AppModule) Name() string                                     { return types.ModuleName }
func (AppModule) RegisterInvariants(_ sdk.InvariantRegistry)       {}
func (AppModule) Route() sdk.Route                                 { return sdk.Route{} }
func (AppModule) QuerierRoute() string                             { return types.QuerierRoute }
func (AppModule) LegacyQuerierHandler(_ interface{}) sdk.Querier   { return nil }
func (AppModule) RegisterServices(_ module.Configurator)           {}
func (AppModule) ConsensusVersion() uint64                         { return 1 }
func (AppModule) GenerateGenesisState(_ *module.SimulationState)   {}
func (AppModule) ProposalContents(_ module.SimulationState) []simtypes.WeightedProposalContent {
	return nil
}
func (AppModule) WeightedOperations(_ module.SimulationState) []simtypes.WeightedOperation {
	return nil
}

func (am AppModule) InitGenesis(ctx sdk.Context, cdc codec.JSONCodec, data json.RawMessage) []abci.ValidatorUpdate {
	var gs types.GenesisState
	if err := json.Unmarshal(data, &gs); err != nil {
		panic(err)
	}
	am.keeper.InitGenesis(ctx, gs)
	return []abci.ValidatorUpdate{}
}

func (am AppModule) ExportGenesis(ctx sdk.Context, cdc codec.JSONCodec) json.RawMessage {
	gs := am.keeper.ExportGenesis(ctx)
	return marshalGenesis(cdc, gs)
}

func (AppModule) BeginBlock(_ sdk.Context, _ abci.RequestBeginBlock) {}
func (AppModule) EndBlock(_ sdk.Context, _ abci.RequestEndBlock) []abci.ValidatorUpdate {
	return []abci.ValidatorUpdate{}
}

// ── helpers ───────────────────────────────────────────────────────────────────

func marshalGenesis(_ codec.JSONCodec, gs *types.GenesisState) json.RawMessage {
	bz, err := json.Marshal(gs)
	if err != nil {
		panic(err)
	}
	return bz
}
