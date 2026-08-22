package keeper

import (
	"context"
	"fmt"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

type MsgServer struct {
	Keeper
}

func NewMsgServerImpl(keeper Keeper) types.MsgServer {
	return &MsgServer{Keeper: keeper}
}

func (ms MsgServer) Mint(goCtx context.Context, msg *types.MsgMint) (*types.MsgMintResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)
	recipient, err := sdk.AccAddressFromBech32(msg.Recipient)
	if err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidAddress, err.Error())
	}
	if err := ms.Keeper.Mint(ctx, recipient, msg.Amount, msg.Reason, msg.ActivityID, msg.VerificationHash); err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, err.Error())
	}
	return &types.MsgMintResponse{MintedAmount: msg.Amount.String()}, nil
}

func (ms MsgServer) Burn(goCtx context.Context, msg *types.MsgBurn) (*types.MsgBurnResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)
	sender, err := sdk.AccAddressFromBech32(msg.Sender)
	if err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidAddress, err.Error())
	}
	if err := ms.Keeper.Burn(ctx, sender, msg.Amount, msg.Reason); err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, err.Error())
	}
	return &types.MsgBurnResponse{BurnedAmount: msg.Amount.String()}, nil
}

func (ms MsgServer) Transfer(goCtx context.Context, msg *types.MsgTransfer) (*types.MsgTransferResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidAddress, err.Error())
	}
	to, err := sdk.AccAddressFromBech32(msg.To)
	if err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidAddress, err.Error())
	}
	if err := ms.Keeper.Transfer(ctx, from, to, msg.Amount); err != nil {
		return nil, sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, err.Error())
	}
	return &types.MsgTransferResponse{TransferredAmount: msg.Amount.String()}, nil
}