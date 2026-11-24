package keeper

import (
	"context"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"

	"github.com/decentralized-rights-protocol/drp/chain/x/poat/types"
)

type msgServer struct { keeper Keeper }

// NewMsgServerImpl returns the transaction service backed by the PoAT keeper.
func NewMsgServerImpl(k Keeper) types.MsgServer { return &msgServer{keeper: k} }

var _ types.MsgServer = (*msgServer)(nil)

func (s *msgServer) SubmitActivityProof(goCtx context.Context, msg *types.MsgSubmitActivityProof) (*types.MsgSubmitActivityProofResponse, error) {
	if msg == nil { return nil, sdkerrors.ErrInvalidRequest.Wrap("nil message") }
	if err := msg.ValidateBasic(); err != nil { return nil, err }
	ctx := sdk.UnwrapSDKContext(goCtx)
	proofID := types.BuildProofID(msg.Submitter, msg.CommitmentCID, msg.MetadataHash)
	if _, found := s.keeper.GetActivityProof(ctx, proofID); found {
		return nil, sdkerrors.ErrInvalidRequest.Wrap("activity proof commitment has already been submitted")
	}
	now := ctx.BlockTime().UTC()
	proof := types.ActivityProof{ID: proofID, Submitter: msg.Submitter, CommitmentCID: msg.CommitmentCID,
		ProofType: msg.ProofType, MetadataHash: msg.MetadataHash, Status: types.ProofStatusPending,
		SubmittedAt: now, UpdatedAt: now}
	s.keeper.SetActivityProof(ctx, proof)
	ctx.EventManager().EmitEvent(sdk.NewEvent("poat_activity_proof_submitted",
		sdk.NewAttribute("proof_id", proofID), sdk.NewAttribute("submitter", msg.Submitter),
		sdk.NewAttribute("proof_type", msg.ProofType), sdk.NewAttribute("status", "pending")))
	return &types.MsgSubmitActivityProofResponse{}, nil
}

func (s *msgServer) RevokeActivityProof(goCtx context.Context, msg *types.MsgRevokeActivityProof) (*types.MsgRevokeActivityProofResponse, error) {
	if msg == nil { return nil, sdkerrors.ErrInvalidRequest.Wrap("nil message") }
	if err := msg.ValidateBasic(); err != nil { return nil, err }
	ctx := sdk.UnwrapSDKContext(goCtx)
	proof, found := s.keeper.GetActivityProof(ctx, msg.ProofID)
	if !found { return nil, sdkerrors.ErrNotFound.Wrap("activity proof not found") }
	if proof.Submitter != msg.Authority { return nil, sdkerrors.ErrUnauthorized.Wrap("only the original submitter may revoke this proof") }
	if proof.Status == types.ProofStatusRevoked { return nil, sdkerrors.ErrInvalidRequest.Wrap("activity proof is already revoked") }
	proof.Status = types.ProofStatusRevoked
	proof.UpdatedAt = ctx.BlockTime().UTC()
	s.keeper.SetActivityProof(ctx, proof)
	ctx.EventManager().EmitEvent(sdk.NewEvent("poat_activity_proof_revoked",
		sdk.NewAttribute("proof_id", proof.ID), sdk.NewAttribute("authority", msg.Authority),
		sdk.NewAttribute("reason", msg.Reason), sdk.NewAttribute("status", "revoked")))
	return &types.MsgRevokeActivityProofResponse{}, nil
}
