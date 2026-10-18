package types

import (
	"github.com/cosmos/cosmos-sdk/codec"
	cdctypes "github.com/cosmos/cosmos-sdk/codec/types"
)

// RegisterInterfaces registers the interfaces for the deri module
func RegisterInterfaces(registry cdctypes.InterfaceRegistry) {
	// Message implementations are registered here only after the message types
	// are generated from the module's protobuf definitions. Hand-written structs
	// must not be registered as Cosmos SDK transaction messages.
}

// RegisterLegacyAminoCodec registers the legacy amino codec
func RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	cdc.RegisterConcrete(&MsgTransfer{}, "drp/deri/MsgTransfer", nil)
	cdc.RegisterConcrete(&MsgMint{}, "drp/deri/MsgMint", nil)
	cdc.RegisterConcrete(&MsgBurn{}, "drp/deri/MsgBurn", nil)
}

