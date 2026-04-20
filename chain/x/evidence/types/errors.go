package types

import "errors"

var (
	ErrDuplicateCommitmentID = errors.New("drpevidence: duplicate commitment ID")
	ErrCommitmentNotFound    = errors.New("drpevidence: commitment not found")
	ErrInvalidCID            = errors.New("drpevidence: CID is not a valid CIDv1 string")
	ErrEmptyContentHash      = errors.New("drpevidence: content_hash must not be empty")
	ErrEmptyMetadataHash     = errors.New("drpevidence: metadata_hash must not be empty")
	ErrUnauthorizedRevoke    = errors.New("drpevidence: caller is not authorised to revoke this commitment")
)
