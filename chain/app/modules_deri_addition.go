package app

import (
	"encoding/json"

	"github.com/cosmos/cosmos-sdk/types/module"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/runtime"
	"github.com/spf13/cobra"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/client/cli"
	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/client/rest"
)

// DeriModule defines the module info for the deri module
var DeriModule = &module.Module{
	Basic: module.NewBasicModule(
		deri.ModuleName,
		deri.AppModuleBasic{},
		nil,
	),
	RegisterRESTRoutes: registerDeriRESTRoutes,
	RegisterGRPCGatewayRoutes: registerDeriGRPCGatewayRoutes,
	GetTxCmd:            getDeriTxCmd,
	GetQueryCmd:         getDeriQueryCmd,
}

// registerDeriRESTRoutes registers the REST routes for the deri module
func registerDeriRESTRoutes(clientCtx client.Context, rtr *mux.Router) {
	rest.RegisterRoutes(clientCtx, rtr)
}

// registerDeriGRPCGatewayRoutes registers the gRPC Gateway routes for the deri module
func registerDeriGRPCGatewayRoutes(clientCtx client.Context, mux *runtime.ServeMux) {
	// Deri module doesn't have gRPC Gateway routes yet
	_ = clientCtx
	_ = mux
}

// getDeriTxCmd returns the transaction command for the deri module
func getDeriTxCmd() *cobra.Command {
	return cli.GetTxCmd()
}

// getDeriQueryCmd returns the query command for the deri module
func getDeriQueryCmd() *cobra.Command {
	return cli.GetQueryCmd()
}

// DeriModuleInfo defines the module information for the deri module
func DeriModuleInfo() module.ModuleInfo {
	return module.ModuleInfo{
		Name:       deri.ModuleName,
		NewHandler:  NewDeriHandler,
		NewQuerier:  NewDeriQuerier,
		InitGenesis: InitDeriGenesis,
		ExportGenesis: ExportDeriGenesis,
		BeginBlock:  BeginDeriBlock,
		EndBlock:    EndDeriBlock,
		DefaultGenesis: DefaultDeriGenesis,
		ValidateGenesis: ValidateDeriGenesis,
	}
}

// DefaultDeriGenesis returns the default genesis state for the deri module
func DefaultDeriGenesis() json.RawMessage {
	return deri.DefaultGenesis()
}

// ValidateDeriGenesis validates the genesis state for the deri module
func ValidateDeriGenesis(cdc codec.JSONCodec, config client.TxEncodingConfig, bz json.RawMessage) error {
	return deri.ValidateGenesis(cdc, config, bz)
}

// InitDeriGenesis initializes the deri module from genesis
func InitDeriGenesis(ctx sdk.Context, cdc codec.JSONCodec, genState json.RawMessage) []abci.ValidatorUpdate {
	return deri.InitGenesis(ctx, cdc, genState)
}

// ExportDeriGenesis exports the deri module state to genesis format
func ExportDeriGenesis(ctx sdk.Context, cdc codec.JSONCodec) json.RawMessage {
	return deri.ExportGenesis(ctx, cdc)
}

// BeginDeriBlock performs actions at the beginning of a block for the deri module
func BeginDeriBlock(ctx sdk.Context, req abci.RequestBeginBlock) {
	// No-op for now
	_ = ctx
	_ = req
}

// EndDeriBlock performs actions at the end of a block for the deri module
func EndDeriBlock(ctx sdk.Context, req abci.RequestEndBlock) []abci.ValidatorUpdate {
	// No-op for now
	_ = ctx
	_ = req
	return []abci.ValidatorUpdate{}
}

// NewDeriHandler returns the handler for the deri module
func NewDeriHandler(keeper deri.Keeper) sdk.Handler {
	return func(ctx sdk.Context, msg sdk.Msg) (*sdk.Result, error) {
		// Route messages to the appropriate handler
		switch msg := msg.(type) {
		case *deri.MsgTransfer:
			return handleMsgTransfer(ctx, keeper, msg)
		case *deri.MsgMint:
			return handleMsgMint(ctx, keeper, msg)
		case *deri.MsgBurn:
			return handleMsgBurn(ctx, keeper, msg)
		default:
			return nil, sdk.ErrUnknownRequest.Wrapf("unknown message type: %T", msg)
		}
	}
}

// handleMsgTransfer handles MsgTransfer messages
func handleMsgTransfer(ctx sdk.Context, keeper deri.Keeper, msg *deri.MsgTransfer) (*sdk.Result, error) {
	// Parse amount
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return nil, sdk.ErrInvalidRequest.Wrapf("invalid amount: %s", msg.Amount)
	}

	// Get addresses
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid from address: %s", msg.From)
	}

	to, err := sdk.AccAddressFromBech32(msg.To)
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid to address: %s", msg.To)
	}

	// Perform transfer
	if err := keeper.Transfer(ctx, from, to, amount); err != nil {
		return nil, err
	}

	return &sdk.Result{Data: []byte("transfer successful")}, nil
}

// handleMsgMint handles MsgMint messages
func handleMsgMint(ctx sdk.Context, keeper deri.Keeper, msg *deri.MsgMint) (*sdk.Result, error) {
	// Parse amount
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return nil, sdk.ErrInvalidRequest.Wrapf("invalid amount: %s", msg.Amount)
	}

	// Get addresses
	to, err := sdk.AccAddressFromBech32(msg.To)
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid to address: %s", msg.To)
	}

	signer, err := sdk.AccAddressFromBech32(msg.Signer)
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid signer address: %s", msg.Signer)
	}

	// Verify the signer is authorized
	if !keeper.IsAuthorizedMinter(ctx, signer) {
		return nil, sdk.ErrUnauthorized.Wrapf("signer %s is not authorized to mint", msg.Signer)
	}

	// Perform mint
	if err := keeper.Mint(ctx, to, amount, msg.Reason); err != nil {
		return nil, err
	}

	return &sdk.Result{Data: []byte("mint successful")}, nil
}

// handleMsgBurn handles MsgBurn messages
func handleMsgBurn(ctx sdk.Context, keeper deri.Keeper, msg *deri.MsgBurn) (*sdk.Result, error) {
	// Parse amount
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return nil, sdk.ErrInvalidRequest.Wrapf("invalid amount: %s", msg.Amount)
	}

	// Get address
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid from address: %s", msg.From)
	}

	// Perform burn
	if err := keeper.Burn(ctx, from, amount, msg.Reason); err != nil {
		return nil, err
	}

	return &sdk.Result{Data: []byte("burn successful")}, nil
}

// NewDeriQuerier returns the querier for the deri module
func NewDeriQuerier(keeper deri.Keeper) sdk.Querier {
	return func(ctx sdk.Context, path []string, req abci.RequestQuery) ([]byte, error) {
		// Route queries to the appropriate handler
		switch path[0] {
		case "balance":
			return queryBalance(ctx, keeper, path, req)
		case "total-supply":
			return queryTotalSupply(ctx, keeper, path, req)
		case "params":
			return queryParams(ctx, keeper, path, req)
		default:
			return nil, sdk.ErrUnknownRequest.Wrapf("unknown query path: %s", path[0])
		}
	}
}

// queryBalance handles balance queries
func queryBalance(ctx sdk.Context, keeper deri.Keeper, path []string, req abci.RequestQuery) ([]byte, error) {
	if len(path) < 2 {
		return nil, sdk.ErrInvalidRequest.Wrap("address is required")
	}

	address, err := sdk.AccAddressFromBech32(path[1])
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid address: %s", path[1])
	}

	balance := keeper.GetBalance(ctx, address)

	return []byte(balance.String()), nil
}

// queryTotalSupply handles total supply queries
func queryTotalSupply(ctx sdk.Context, keeper deri.Keeper, path []string, req abci.RequestQuery) ([]byte, error) {
	_ = path
	_ = req

	totalSupply := keeper.GetTotalSupply(ctx)

	return []byte(totalSupply.String()), nil
}

// queryParams handles params queries
func queryParams(ctx sdk.Context, keeper deri.Keeper, path []string, req abci.RequestQuery) ([]byte, error) {
	_ = path
	_ = req

	params, err := keeper.GetParams(ctx)
	if err != nil {
		return nil, err
	}

	return []byte(params.String()), nil
}
