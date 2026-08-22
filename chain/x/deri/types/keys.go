package types

import (
	"fmt"

	"github.com/cosmos/cosmos-sdk/types"
)

const (
	MintAuthorityKey   = "mint_authority"
	EmissionLimitsKey  = "emission_limits"
	TotalSupplyKey      = "total_supply"
	BalancePrefix       = "balance/"
)

func BalanceKey(addr types.AccAddress) []byte {
	return []byte(fmt.Sprintf("%s%s", BalancePrefix, addr.String()))
}