package types

import (
	"github.com/cosmos/cosmos-sdk/codec"
	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
)

var (
	amino     = codec.NewLegacyAmino()
	ModuleCdc = codec.NewAminoCodec(amino)
)

func init() {
	RegisterLegacyAminoCodec(amino)
	sdk.RegisterLegacyAminoCodec(amino)
}

func RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	cdc.RegisterConcrete(&MsgAnchorEvidence{}, "drpevidence/AnchorEvidence", nil)
	cdc.RegisterConcrete(&MsgRevokeEvidence{}, "drpevidence/RevokeEvidence", nil)
}

func RegisterInterfaces(registry codectypes.InterfaceRegistry) {
	// NOTE: Placeholder (non-proto-generated) Msgs; disable interface-registry wiring
	// until proper protobuf types exist to avoid typeURL collisions at runtime.
	//
	// registry.RegisterImplementations((*sdk.Msg)(nil),
	//   &MsgAnchorEvidence{},
	//   &MsgRevokeEvidence{},
	// )
	_ = registry
	_ = sdk.Msg(nil)
}
