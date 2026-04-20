// Package trust implements the Trust State Cosmos SDK module.
package trust

import (
	"encoding/json"

	"github.com/spf13/cobra"
	abci "github.com/cometbft/cometbft/abci/types"

	"github.com/cosmos/cosmos-sdk/codec"
	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	simtypes "github.com/cosmos/cosmos-sdk/types/simulation"

	"github.com/decentralized-rights-protocol/drp/chain/x/trust/keeper"
	"github.com/decentralized-rights-protocol/drp/chain/x/trust/types"
)

var (
	_ module.AppModuleBasic = AppModuleBasic{}
	_ module.AppModule      = AppModule{}
)

type AppModuleBasic struct{}

func (AppModuleBasic) Name() string { return types.ModuleName }
func (AppModuleBasic) RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	types.RegisterLegacyAminoCodec(cdc)
}
func (AppModuleBasic) RegisterInterfaces(r codectypes.InterfaceRegistry) { types.RegisterInterfaces(r) }
func (AppModuleBasic) DefaultGenesis(_ codec.JSONCodec) json.RawMessage {
	bz, _ := json.Marshal(types.DefaultGenesis())
	return bz
}
func (AppModuleBasic) ValidateGenesis(_ codec.JSONCodec, _ interface{}, bz json.RawMessage) error {
	var gs types.GenesisState
	return json.Unmarshal(bz, &gs)
}
func (AppModuleBasic) RegisterGRPCGatewayRoutes(_ interface{}, _ interface{}) {}
func (AppModuleBasic) GetTxCmd() *cobra.Command                               { return nil }
func (AppModuleBasic) GetQueryCmd() *cobra.Command                            { return nil }

type AppModule struct {
	AppModuleBasic
	cdc    codec.Codec
	keeper keeper.Keeper
}

func NewAppModule(cdc codec.Codec, k keeper.Keeper) AppModule { return AppModule{cdc: cdc, keeper: k} }
func (AppModule) Name() string                               { return types.ModuleName }
func (AppModule) RegisterInvariants(_ sdk.InvariantRegistry) {}
func (AppModule) Route() sdk.Route                           { return sdk.Route{} }
func (AppModule) QuerierRoute() string                       { return types.QuerierRoute }
func (AppModule) LegacyQuerierHandler(_ interface{}) sdk.Querier { return nil }
func (AppModule) RegisterServices(_ module.Configurator)         {}
func (AppModule) ConsensusVersion() uint64                       { return 1 }
func (AppModule) GenerateGenesisState(_ *module.SimulationState) {}
func (AppModule) ProposalContents(_ module.SimulationState) []simtypes.WeightedProposalContent {
	return nil
}
func (AppModule) WeightedOperations(_ module.SimulationState) []simtypes.WeightedOperation {
	return nil
}
func (am AppModule) InitGenesis(ctx sdk.Context, _ codec.JSONCodec, data json.RawMessage) []abci.ValidatorUpdate {
	var gs types.GenesisState
	if err := json.Unmarshal(data, &gs); err != nil {
		panic(err)
	}
	am.keeper.InitGenesis(ctx, gs)
	return []abci.ValidatorUpdate{}
}
func (am AppModule) ExportGenesis(ctx sdk.Context, _ codec.JSONCodec) json.RawMessage {
	bz, _ := json.Marshal(am.keeper.ExportGenesis(ctx))
	return bz
}
func (AppModule) BeginBlock(_ sdk.Context, _ abci.RequestBeginBlock) {}
func (AppModule) EndBlock(_ sdk.Context, _ abci.RequestEndBlock) []abci.ValidatorUpdate {
	return []abci.ValidatorUpdate{}
}
