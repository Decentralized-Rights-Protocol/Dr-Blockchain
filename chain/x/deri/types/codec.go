package types

import (
	"github.com/cosmos/cosmos-sdk/codec"
	cdctypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/msgservice"
)

// RegisterInterfaces registers the interfaces for the deri module
func RegisterInterfaces(registry cdctypes.InterfaceRegistry) {
	registry.RegisterImplementations(
		(*sdk.Msg)(nil),
		&MsgTransfer{},
		&MsgMint{},
		&MsgBurn{},
	)

	msgservice.RegisterMsgServiceDesc(registry, &_Msg_serviceDesc)
}

// RegisterLegacyAminoCodec registers the legacy amino codec
func RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	cdc.RegisterConcrete(&MsgTransfer{}, "drp/deri/MsgTransfer", nil)
	cdc.RegisterConcrete(&MsgMint{}, "drp/deri/MsgMint", nil)
	cdc.RegisterConcrete(&MsgBurn{}, "drp/deri/MsgBurn", nil)
}

// RegisterGRPCGatewayRoutes registers the gRPC Gateway routes
func RegisterGRPCGatewayRoutes(clientCtx sdk.ClientContext, mux *sdk.GRPCGatewayRouter) {
	// Register query routes
	_ = clientCtx
	_ = mux
	// TODO: Implement gRPC Gateway routes
}
