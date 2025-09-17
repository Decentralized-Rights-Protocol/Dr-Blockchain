import grpc
from concurrent import futures
import time

from . import drp_pb2
from . import drp_pb2_grpc

# Simple in-memory storage
BLOCKCHAIN = []
MEMPOOL = []

class DrpNodeServicer(drp_pb2_grpc.DrpNodeServicer):
    def BroadcastTransaction(self, request, context):
        # Mock validation: accept everything
        MEMPOOL.append(request)
        print(f"[Transaction] Received: {request.id} from {request.sender} to {request.receiver}")
        return drp_pb2.Ack(success=True, message="Transaction broadcasted")

    def SubmitBlock(self, request, context):
        # Very naive chain acceptance (no real consensus)
        BLOCKCHAIN.append(request)
        print(f"[Block] Submitted: index={request.index} hash={request.hash} by {request.miner}")
        return drp_pb2.Ack(success=True, message="Block accepted")

    def Ping(self, request, context):
        print(f"[Heartbeat] Node {request.node_id} status: {request.status}")
        return drp_pb2.Ack(success=True, message="Pong")

    def RequestActivityVerification(self, request, context):
        print(f"[Verify] Activity request from user {request.user_id} type {request.activity_type}")
        # Mock logic: accept if metadata contains "valid"
        if "valid" in request.metadata.lower():
            return drp_pb2.VerificationResponse(valid=True, reason="Verified by AI mock")
        else:
            return drp_pb2.VerificationResponse(valid=False, reason="Failed heuristic checks")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    drp_pb2_grpc.add_DrpNodeServicer_to_server(DrpNodeServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("DRP gRPC server started on :50051")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
