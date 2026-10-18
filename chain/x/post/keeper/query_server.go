package keeper

import (
	"context"
	"encoding/json"

	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/decentralized-rights-protocol/drp/chain/x/post/types"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// queryServer returns existing keeper records as opaque JSON without migrating state.
// Params remains Unimplemented because InitGenesis does not persist parameters.
type queryServer struct {
	types.UnimplementedQueryServer
	keeper Keeper
}

var _ types.QueryServer = (*queryServer)(nil)

func NewQueryServer(k Keeper) types.QueryServer { return &queryServer{keeper: k} }

func (s queryServer) StatusRecord(ctx context.Context, req *types.QueryStatusRecordRequest) (*types.QueryStatusRecordResponse, error) {
	if req == nil {
		return nil, status.Error(codes.InvalidArgument, "request must not be nil")
	}
	if req.RecordId == "" {
		return nil, status.Error(codes.InvalidArgument, "record_id must not be empty")
	}
	record, found := s.keeper.GetStatusRecord(sdk.UnwrapSDKContext(ctx), req.RecordId)
	if !found {
		return nil, status.Error(codes.NotFound, "post record not found")
	}
	data, err := json.Marshal(record)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to encode record JSON")
	}
	return &types.QueryStatusRecordResponse{RecordJson: data}, nil
}
