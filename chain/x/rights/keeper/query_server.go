package keeper

import (
	"context"
	"encoding/json"

	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/decentralized-rights-protocol/drp/chain/x/rights/types"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// queryServer returns existing keeper records as opaque JSON without migrating state.
// Params remains Unimplemented because InitGenesis does not persist parameters.
type queryServer struct {
	types.UnimplementedQueryServer
	keeper Keeper
}

var _ types.QueryServer = queryServer{}

func NewQueryServer(k Keeper) types.QueryServer { return queryServer{keeper: k} }

func (s queryServer) Proposal(ctx context.Context, req *types.QueryProposalRequest) (*types.QueryProposalResponse, error) {
	if req == nil {
		return nil, status.Error(codes.InvalidArgument, "request must not be nil")
	}
	record, found := s.keeper.GetProposal(sdk.UnwrapSDKContext(ctx), req.ProposalID)
	if !found {
		return nil, status.Error(codes.NotFound, "rights record not found")
	}
	data, err := json.Marshal(record)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to encode record JSON")
	}
	return &types.QueryProposalResponse{RecordJson: data}, nil
}
