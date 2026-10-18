package keeper

import (
	"context"
	"encoding/json"

	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/decentralized-rights-protocol/drp/chain/x/poat/types"
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

func (s queryServer) ActivityProof(ctx context.Context, req *types.QueryActivityProofRequest) (*types.QueryActivityProofResponse, error) {
	if req == nil {
		return nil, status.Error(codes.InvalidArgument, "request must not be nil")
	}
	if req.ProofID == "" {
		return nil, status.Error(codes.InvalidArgument, "proof_id must not be empty")
	}
	record, found := s.keeper.GetActivityProof(sdk.UnwrapSDKContext(ctx), req.ProofID)
	if !found {
		return nil, status.Error(codes.NotFound, "poat record not found")
	}
	data, err := json.Marshal(record)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to encode record JSON")
	}
	return &types.QueryActivityProofResponse{RecordJson: data}, nil
}
