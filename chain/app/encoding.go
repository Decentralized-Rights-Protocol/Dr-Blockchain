// Package app defines the DRP application wiring for the Cosmos SDK.
package app

import (
	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/codec"
	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	cryptocodec "github.com/cosmos/cosmos-sdk/crypto/codec"
	txtypes "github.com/cosmos/cosmos-sdk/types/tx"
	"github.com/cosmos/cosmos-sdk/x/auth/tx"
)

// EncodingConfig specifies the concrete encoding types to use for DRP.
// This struct is intentionally kept thin: we evolve it deliberately as
// DRP adds new message types and interface registrations.
type EncodingConfig struct {
	InterfaceRegistry codectypes.InterfaceRegistry
	Marshaler         codec.Codec
	TxConfig          client.TxConfig
	Amino             *codec.LegacyAmino
}

// MakeEncodingConfig creates the default DRP EncodingConfig.
// All Cosmos SDK standard interfaces and DRP module interfaces will be
// registered here as modules are wired into the app.
func MakeEncodingConfig() EncodingConfig {
	amino := codec.NewLegacyAmino()
	interfaceRegistry := codectypes.NewInterfaceRegistry()

	// Register crypto (PubKey/PrivKey) types for both Amino and Protobuf Any packing.
	// This is required for keyring operations (`drpd keys ...`) to work correctly.
	cryptocodec.RegisterCrypto(amino)
	cryptocodec.RegisterInterfaces(interfaceRegistry)
	txtypes.RegisterInterfaces(interfaceRegistry)

	// Register standard SDK Amino types (includes legacy Msg, accounts, etc).
	sdk.RegisterLegacyAminoCodec(amino)

	marshaler := codec.NewProtoCodec(interfaceRegistry)
	txCfg := tx.NewTxConfig(marshaler, tx.DefaultSignModes)

	return EncodingConfig{
		InterfaceRegistry: interfaceRegistry,
		Marshaler:         marshaler,
		TxConfig:          txCfg,
		Amino:             amino,
	}
}

// DefaultNodeHome is the default home directory for the drpd binary.
// Overridable via --home flag or the DRPD_HOME env variable.
const DefaultNodeHome = ".drpd"
