package types

import (
	"context"
	"reflect"
	"testing"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	codectypes "github.com/cosmos/cosmos-sdk/codec/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/gogoproto/proto"
)

func TestMessageWireAndAnyRoundTrip(t *testing.T) {
	registry := codectypes.NewInterfaceRegistry()
	RegisterInterfaces(registry)
	messages := []sdk.Msg{&MsgIssueTrustStatus{Issuer: "issuer", Subject: "subject", StatusLevel: "status_level", BasisCID: "basis_cid"}, &MsgRevokeTrustStatus{Authority: "authority", RecordID: "record_id", Reason: "reason"}}
	for _, msg := range messages {
		t.Run(proto.MessageName(msg), func(t *testing.T) {
			if proto.MessageName(msg) == "" {
				t.Fatal("missing generated message name")
			}
			wire, err := proto.Marshal(msg)
			if err != nil {
				t.Fatal(err)
			}
			decoded := reflect.New(reflect.TypeOf(msg).Elem()).Interface().(sdk.Msg)
			if err := proto.Unmarshal(wire, decoded); err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(msg, decoded) {
				t.Fatalf("wire roundtrip changed message: %v", decoded)
			}
			packed, err := codectypes.NewAnyWithValue(msg)
			if err != nil {
				t.Fatal(err)
			}
			// Clear the cached value so unpacking must use registered protobuf types.
			packed = &codectypes.Any{TypeUrl: packed.TypeUrl, Value: packed.Value}
			var unpacked sdk.Msg
			if err := registry.UnpackAny(packed, &unpacked); err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(msg, unpacked) {
				t.Fatalf("Any roundtrip changed message: %v", unpacked)
			}
		})
	}
}

// Generated registration must expose both services; scaffold Params cannot
// report defaults as if they were persisted governance parameters.
func TestGeneratedServiceRegistration(t *testing.T) {
	server := grpc.NewServer()
	RegisterMsgServer(server, &UnimplementedMsgServer{})
	RegisterQueryServer(server, &UnimplementedQueryServer{})
	services := server.GetServiceInfo()
	for _, name := range []string{"drp.post.Msg", "drp.post.Query"} {
		if len(services[name].Methods) == 0 {
			t.Fatalf("service %s has no registered methods", name)
		}
	}
	query := &UnimplementedQueryServer{}
	if _, err := query.Params(context.Background(), &QueryParamsRequest{}); status.Code(err) != codes.Unimplemented {
		t.Fatalf("Params returned %v, want Unimplemented", err)
	}
}
