package types

import (
	"github.com/cosmos/cosmos-sdk/codec"
	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/msgservice"
)

var (
	amino     = codec.NewLegacyAmino()
	ModuleCdc = codec.NewAminoCodec(amino)
)

func init() {
	RegisterLegacyAminoCodec(amino)
	sdk.RegisterLegacyAminoCodec(amino)
}

// RegisterLegacyAminoCodec registers PoAT message types with the legacy amino codec.
func RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	cdc.RegisterConcrete(&MsgSubmitActivityProof{}, "poat/SubmitActivityProof", nil)
	cdc.RegisterConcrete(&MsgRevokeActivityProof{}, "poat/RevokeActivityProof", nil)
}

// RegisterInterfaces registers PoAT messages with the Cosmos SDK interface registry.
func RegisterInterfaces(registry codectypes.InterfaceRegistry) {
	registry.RegisterImplementations((*sdk.Msg)(nil), &MsgSubmitActivityProof{}, &MsgRevokeActivityProof{})
	msgservice.RegisterMsgServiceDesc(registry, &_Msg_serviceDesc)
}
