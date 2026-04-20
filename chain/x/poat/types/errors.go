package types

import "errors"

// Sentinel errors for the PoAT module.
var (
	ErrDuplicateProofID   = errors.New("poat: duplicate proof ID in genesis")
	ErrInvalidCID         = errors.New("poat: commitment_cid is not a valid CID")
	ErrProofNotFound      = errors.New("poat: activity proof not found")
	ErrUnauthorized       = errors.New("poat: caller is not authorised to perform this action")
	ErrInvalidProofType   = errors.New("poat: proof_type is not in the allowed set")
)
