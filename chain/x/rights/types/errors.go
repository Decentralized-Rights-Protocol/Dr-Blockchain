package types

import "errors"

var (
	ErrProposalNotFound     = errors.New("rights: proposal not found")
	ErrInvalidProposalTitle = errors.New("rights: proposal title must not be empty")
	ErrUnauthorized         = errors.New("rights: caller is not authorised")
)
