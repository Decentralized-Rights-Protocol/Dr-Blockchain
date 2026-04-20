package types

import "errors"

var (
	ErrTrustStateNotFound = errors.New("trust: trust state not found for address")
	ErrInvalidScore       = errors.New("trust: trust score must be non-negative")
)
