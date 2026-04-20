package types

import "errors"

var (
	ErrDuplicateRecordID   = errors.New("post: duplicate status record ID in genesis")
	ErrRecordNotFound      = errors.New("post: status record not found")
	ErrNonTransferable     = errors.New("post: status records are non-transferable")
	ErrUnauthorizedIssuer  = errors.New("post: caller is not an authorised issuer")
)
