package deri

import (
	"context"
	"encoding/json"

	abci "github.com/cometbft/cometbft/abci/types"
	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/codec"
	cdctypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/runtime"
	"github.com/spf13/cobra"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/client/cli"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/client/rest"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/keeper"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// ModuleName is the name of the module
const ModuleName = types.ModuleName

// ConsensusVersion defines the module consensus version
const ConsensusVersion = 1

var (
	_ module.AppModule      = AppModule{}
	_ module.AppModuleBasic = AppModuleBasic{}
)

// AppModuleBasic defines the basic application module
// used by the app builder

type AppModuleBasic struct {
	cdc codec.Codec
}

// Name returns the module name
func (AppModuleBasic) Name() string {
	return ModuleName
}

// RegisterLegacyAminoCodec registers the legacy amino codec
func (AppModuleBasic) RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	types.RegisterLegacyAminoCodec(cdc)
}

// RegisterInterfaces registers the module interfaces
func (AppModuleBasic) RegisterInterfaces(registry cdctypes.InterfaceRegistry) {
	types.RegisterInterfaces(registry)
}

// DefaultGenesis returns the default genesis state
func (AppModuleBasic) DefaultGenesis(cdc codec.JSONCodec) json.RawMessage {
	return cdc.MustMarshalJSON(types.DefaultGenesisState())
}

// ValidateGenesis performs genesis state validation
func (AppModuleBasic) ValidateGenesis(cdc codec.JSONCodec, config client.TxEncodingConfig, bz json.RawMessage) error {
	var genState types.GenesisState
	if err := cdc.UnmarshalJSON(bz, &genState); err != nil {
		return err
	}
	return genState.Validate()
}

// RegisterRESTRoutes registers the REST routes
func (AppModuleBasic) RegisterRESTRoutes(clientCtx client.Context, rtr *mux.Router) {
	rest.RegisterRoutes(clientCtx, rtr)
}

// RegisterGRPCGatewayRoutes registers the gRPC Gateway routes
func (AppModuleBasic) RegisterGRPCGatewayRoutes(clientCtx client.Context, mux *runtime.ServeMux) {
	// Register query routes
	types.RegisterQueryHandlerClient(context.Background(), mux, types.NewQueryClient(clientCtx))
}

// GetTxCmd returns the root tx command for the module
func (AppModuleBasic) GetTxCmd() *cobra.Command {
	return cli.GetTxCmd()
}

// GetQueryCmd returns the root query command for the module
func (AppModuleBasic) GetQueryCmd() *cobra.Command {
	return cli.GetQueryCmd()
}

// InterfaceRegistry returns the module interface registry
func (AppModuleBasic) InterfaceRegistry() cdctypes.InterfaceRegistry {
	return types.InterfaceRegistry()
}

// AppModule defines the full application module
// used by the app builder

type AppModule struct {
	AppModuleBasic

	keeper        keeper.Keeper
	accountKeeper types.AccountKeeper
	bankKeeper    types.BankKeeper
}

// NewAppModule creates a new AppModule instance
func NewAppModule(cdc codec.Codec, keeper keeper.Keeper, accountKeeper types.AccountKeeper, bankKeeper types.BankKeeper) AppModule {
	return AppModule{
		AppModuleBasic: AppModuleBasic{cdc: cdc},
		keeper:         keeper,
		accountKeeper:  accountKeeper,
		bankKeeper:     bankKeeper,
	}
}

// RegisterServices registers the module services
func (am AppModule) RegisterServices(cfg module.Configurator) {
	// Register Msg service
	types.RegisterMsgServer(cfg.MsgServer(), keeper.NewMsgServerImpl(am.keeper))
	
	// Register Query service
	types.RegisterQueryServer(cfg.QueryServer(), keeper.NewQueryServerImpl(am.keeper))

	// Register module
	cfg.RegisterService(types._Msg_serviceDesc)
}

// RegisterInvariants registers the module invariants
func (am AppModule) RegisterInvariants(ir types.InvariantRegistry) {
	// Register invariants
	// ir.RegisterRoute(types.ModuleName, "total-supply", keeper.TotalSupplyInvariant(am.keeper))
}

// InitGenesis performs module initialization from genesis
func (am AppModule) InitGenesis(ctx sdk.Context, cdc codec.JSONCodec, genState json.RawMessage) []abci.ValidatorUpdate {
	var genState types.GenesisState
	cdc.MustUnmarshalJSON(genState, genState)
	am.keeper.InitGenesis(ctx, &genState)
	return []abci.ValidatorUpdate{}
}

// ExportGenesis exports the module state to genesis format
func (am AppModule) ExportGenesis(ctx sdk.Context, cdc codec.JSONCodec) json.RawMessage {
	genState := am.keeper.ExportGenesis(ctx)
	return cdc.MustMarshalJSON(genState)
}

// BeginBlock performs actions at the beginning of a block
func (am AppModule) BeginBlock(ctx sdk.Context, req abci.RequestBeginBlock) {
	// No-op for now
}

// EndBlock performs actions at the end of a block
func (am AppModule) EndBlock(ctx sdk.Context, req abci.RequestEndBlock) []abci.ValidatorUpdate {
	// No-op for now
	return []abci.ValidatorUpdate{}
}
