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

// RegisterLegacyAminoCodec registers PoAT message types with the legacy amino codec.
func RegisterLegacyAminoCodec(cdc *codec.LegacyAmino) {
	cdc.RegisterConcrete(&MsgSubmitActivityProof{}, "poat/SubmitActivityProof", nil)
	cdc.RegisterConcrete(&MsgRevokeActivityProof{}, "poat/RevokeActivityProof", nil)
}

// RegisterInterfaces registers PoAT messages with the Cosmos SDK interface registry.
// Full gRPC service registration will follow once proto types are generated.
func RegisterInterfaces(registry codectypes.InterfaceRegistry) {
	registry.RegisterImplementations((*sdk.Msg)(nil),
		&MsgSubmitActivityProof{},
		&MsgRevokeActivityProof{},
	)
}
