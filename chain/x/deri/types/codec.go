package types

import (
	"github.com/cosmos/cosmos-sdk/codec"
	cdctypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
)

var ModuleCdc = codec.NewProtoCodec(cdctypes.NewInterfaceRegistry())

func RegisterInterfaces(registry cdctypes.InterfaceRegistry) {
	registry.RegisterImplementations((*sdk.Msg)(nil),
		&MsgMint{},
		&MsgBurn{},
		&MsgTransfer{},
		&MsgSetMintAuthority{},
		&MsgUpdateEmissionLimits{},
	)
}

func RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	cdc.RegisterConcrete(&MsgMint{}, "deri/Mint", nil)
	cdc.RegisterConcrete(&MsgBurn{}, "deri/Burn", nil)
	cdc.RegisterConcrete(&MsgTransfer{}, "deri/Transfer", nil)
	cdc.RegisterConcrete(&MsgSetMintAuthority{}, "deri/SetMintAuthority", nil)
	cdc.RegisterConcrete(&MsgUpdateEmissionLimits{}, "deri/UpdateEmissionLimits", nil)
}