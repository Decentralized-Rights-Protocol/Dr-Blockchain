// Package types defines the x/rights module types.
//
// The rights module provides a DRP-specific governance extension layer.
// It allows rights-focused proposals that carry structured metadata about
// affected rights categories, impacted communities, and required evidence.
//
// This module is designed to complement (not replace) the standard x/gov module.
// Standard governance proposals still work; rights proposals add DRP-specific
// context fields and can enforce evidence anchoring requirements.
package types

const (
	ModuleName   = "rights"
	StoreKey     = ModuleName
	RouterKey    = ModuleName
	QuerierRoute = ModuleName
)

var (
	KeyPrefixProposal   = []byte{0x01}
	KeyPrefixProposalID = []byte{0x02}
)

func ProposalKey(id uint64) []byte {
	bz := make([]byte, 8)
	bz[0] = byte(id >> 56)
	bz[1] = byte(id >> 48)
	bz[2] = byte(id >> 40)
	bz[3] = byte(id >> 32)
	bz[4] = byte(id >> 24)
	bz[5] = byte(id >> 16)
	bz[6] = byte(id >> 8)
	bz[7] = byte(id)
	return append(KeyPrefixProposal, bz...)
}
