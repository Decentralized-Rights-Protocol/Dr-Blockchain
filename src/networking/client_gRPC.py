import grpc
import time
import uuid

from . import drp_pb2
from . import drp_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = drp_pb2_grpc.DrpNodeStub(channel)

        # Ping
        heartbeat = drp_pb2.Heartbeat(node_id="node-1", timestamp=int(time.time()), status="healthy")
        resp = stub.Ping(heartbeat)
        print("Ping response:", resp.message)

        # Broadcast Transaction
        tx = drp_pb2.Transaction(
            id=str(uuid.uuid4()),
            sender="alice_wallet",
            receiver="bob_wallet",
            amount=10.5,
            signature="signature_placeholder",
            timestamp=int(time.time()),
            metadata="some valid activity"
        )
        tx_resp = stub.BroadcastTransaction(tx)
        print("Transaction broadcast:", tx_resp.message)

        # Request Activity Verification
        vr = drp_pb2.VerificationRequest(
            user_id="alice",
            activity_type="teaching",
            media_url="http://example.com/proof.jpg",
            metadata="valid lesson submission"
        )
        verification = stub.RequestActivityVerification(vr)
        print("Verification result:", verification.valid, verification.reason)

        # Submit Block
        block = drp_pb2.Block(
            hash="blockhash123",
            previous_hash="prevhash0",
            index=1,
            timestamp=int(time.time()),
            miner="miner_01",
            nonce=42,
            status_proof="proof_of_status_example"
        )
        # include one transaction
        block.transactions.extend([tx])
        block_resp = stub.SubmitBlock(block)
        print("Block submission:", block_resp.message)

if __name__ == "__main__":
    run()
