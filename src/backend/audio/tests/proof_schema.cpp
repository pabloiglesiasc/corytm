#include "proof.pb.h"

#include <string>

using corytm::schemas::proof::ProofMessage;

int main()
{
    ProofMessage original;
    original.set_schema_version (1);
    original.set_payload ("corytm-protobuf-toolchain-proof");

    std::string serialized;
    const bool serialized_ok = original.SerializeToString (&serialized);

    ProofMessage decoded;
    const bool parsed_ok = decoded.ParseFromString (serialized);

    return serialized_ok && parsed_ok
                   && decoded.schema_version() == original.schema_version()
                   && decoded.payload() == original.payload()
               ? 0
               : 1;
}
