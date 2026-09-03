from corytm.generated.proof_pb2 import ProofMessage


def test_proof_message_round_trips() -> None:
    original = ProofMessage(schema_version=1, payload="corytm-protobuf-toolchain-proof")

    decoded = ProofMessage()
    decoded.ParseFromString(original.SerializeToString())

    assert decoded == original
    assert decoded.schema_version == 1
    assert decoded.payload == "corytm-protobuf-toolchain-proof"
