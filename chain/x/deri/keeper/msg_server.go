package keeper

import (
	"context"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"

	"github.com/decentralized-rights-protocol/drp/chain/x/deri/types"
)

// msgServer is the server API for Msg service
// It implements the deri.Msg service
type msgServer struct {
	Keeper
}

// NewMsgServerImpl returns an implementation of the MsgServer interface
// for the provided Keeper
func NewMsgServerImpl(keeper Keeper) types.MsgServer {
	return &msgServer{Keeper: keeper}
}

var _ types.MsgServer = msgServer{}

// Transfer implements the Msg/Transfer RPC method
func (s msgServer) Transfer(goCtx context.Context, msg *types.MsgTransfer) (*types.MsgTransferResponse, error) {
	if msg == nil {
		return nil, sdkerrors.ErrInvalidRequest.Wrap("nil message")
	}
	if err := msg.ValidateBasic(); err != nil {
		return nil, err
	}
	ctx := sdk.UnwrapSDKContext(goCtx)

	// Parse amount
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return nil, sdkerrors.ErrInvalidRequest.Wrapf("invalid amount: %s", msg.Amount)
	}

	// Get addresses
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		return nil, sdkerrors.ErrInvalidAddress.Wrapf("invalid from address: %s", msg.From)
	}

	to, err := sdk.AccAddressFromBech32(msg.To)
	if err != nil {
		return nil, sdkerrors.ErrInvalidAddress.Wrapf("invalid to address: %s", msg.To)
	}

	// Perform transfer
	if err := s.Keeper.Transfer(ctx, from, to, amount); err != nil {
		return nil, err
	}

	return &types.MsgTransferResponse{
		Success: true,
		Error:   "",
	}, nil
}

// Mint implements the Msg/Mint RPC method
// This is restricted to authorized module accounts only
func (s msgServer) Mint(goCtx context.Context, msg *types.MsgMint) (*types.MsgMintResponse, error) {
	if msg == nil {
		return nil, sdkerrors.ErrInvalidRequest.Wrap("nil message")
	}
	if err := msg.ValidateBasic(); err != nil {
		return nil, err
	}
	ctx := sdk.UnwrapSDKContext(goCtx)

	// Parse amount
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return nil, sdkerrors.ErrInvalidRequest.Wrapf("invalid amount: %s", msg.Amount)
	}

	// Get addresses
	to, err := sdk.AccAddressFromBech32(msg.To)
	if err != nil {
		return nil, sdkerrors.ErrInvalidAddress.Wrapf("invalid to address: %s", msg.To)
	}

	signer, err := sdk.AccAddressFromBech32(msg.Signer)
	if err != nil {
		return nil, sdkerrors.ErrInvalidAddress.Wrapf("invalid signer address: %s", msg.Signer)
	}

	// Fail closed until the authority policy and its execution path are defined.
	if !s.Keeper.IsAuthorizedMinter(ctx, signer) {
		return nil, sdkerrors.ErrUnauthorized.Wrapf("signer %s is not authorized to mint", msg.Signer)
	}

	// Perform mint
	if err := s.Keeper.Mint(ctx, to, amount, msg.Reason); err != nil {
		return nil, err
	}

	return &types.MsgMintResponse{
		Success:      true,
		Error:        "",
		MintedAmount: msg.Amount,
	}, nil
}

// Burn implements the Msg/Burn RPC method
func (s msgServer) Burn(goCtx context.Context, msg *types.MsgBurn) (*types.MsgBurnResponse, error) {
	if msg == nil {
		return nil, sdkerrors.ErrInvalidRequest.Wrap("nil message")
	}
	if err := msg.ValidateBasic(); err != nil {
		return nil, err
	}
	ctx := sdk.UnwrapSDKContext(goCtx)

	// Parse amount
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return nil, sdkerrors.ErrInvalidRequest.Wrapf("invalid amount: %s", msg.Amount)
	}

	// Get address
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		return nil, sdkerrors.ErrInvalidAddress.Wrapf("invalid from address: %s", msg.From)
	}

	// Perform burn
	if err := s.Keeper.Burn(ctx, from, amount, msg.Reason); err != nil {
		return nil, err
	}

	return &types.MsgBurnResponse{
		Success:      true,
		Error:        "",
		BurnedAmount: msg.Amount,
	}, nil
}
