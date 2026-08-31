package types

import (
	sdk "github.com/cosmos/cosmos-sdk/types"
)

// Store keys for the deri module
const (
	// StoreKey is the prefix for the deri module store
	StoreKey = ModuleName

	// RouterKey is the message router key for the deri module
	RouterKey = ModuleName

	// MemStoreKey is the memory store key for the deri module
	MemStoreKey = "mem_deri"
)

// KVStore key prefixes
var (
	// KeyPrefixBalance stores the balance of each account
	KeyPrefixBalance = []byte{0x01}

	// KeyPrefixTotalSupply stores the total supply of $DeRi
	KeyPrefixTotalSupply = []byte{0x02}

	// KeyPrefixParams stores the module parameters
	KeyPrefixParams = []byte{0x03}

	// KeyPrefixMintHistory stores the mint history for auditing
	KeyPrefixMintHistory = []byte{0x04}

	// KeyPrefixBurnHistory stores the burn history for auditing
	KeyPrefixBurnHistory = []byte{0x05}
)

// GetBalanceKey returns the key for an account's balance
func GetBalanceKey(address sdk.AccAddress) []byte {
	return append(KeyPrefixBalance, address.Bytes()...)
}

// GetTotalSupplyKey returns the key for the total supply
func GetTotalSupplyKey() []byte {
	return KeyPrefixTotalSupply
}

// GetParamsKey returns the key for the module parameters
func GetParamsKey() []byte {
	return KeyPrefixParams
}

// GetMintHistoryKey returns the key for mint history at a specific height
func GetMintHistoryKey(height int64) []byte {
	return append(KeyPrefixMintHistory, sdk.Uint64ToBigEndian(uint64(height))...)
}

// GetBurnHistoryKey returns the key for burn history at a specific height
func GetBurnHistoryKey(height int64) []byte {
	return append(KeyPrefixBurnHistory, sdk.Uint64ToBigEndian(uint64(height))...)
}
