#include "proof.pb.h"

#include <juce_events/juce_events.h>

#include <condition_variable>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <string>

using corytm::schemas::proof::ProofMessage;

namespace
{
    constexpr juce::uint32 transportMagicNumber = 0x636f7274;
    constexpr int connectTimeoutMs = 5000;
    constexpr int roundTripTimeoutMs = 5000;

    class TransportProofConnection final : public juce::InterprocessConnection
    {
    public:
        explicit TransportProofConnection (std::string secretToSend)
            : juce::InterprocessConnection (false, transportMagicNumber),
              secret (std::move (secretToSend))
        {
        }

        ~TransportProofConnection() override { disconnect(); }

        bool waitForRoundTrip (int timeoutMs)
        {
            std::unique_lock<std::mutex> lock (mutex);
            return conditionVariable.wait_for (lock, std::chrono::milliseconds (timeoutMs), [this]
            {
                return roundTripSucceeded || connectionWasLost;
            })
                   && roundTripSucceeded;
        }

    private:
        void connectionMade() override
        {
            sendMessage (juce::MemoryBlock (secret.data(), secret.size()));
        }

        void connectionLost() override
        {
            const std::lock_guard<std::mutex> lock (mutex);
            connectionWasLost = true;
            conditionVariable.notify_all();
        }

        void messageReceived (const juce::MemoryBlock& message) override
        {
            ProofMessage command;

            if (! command.ParseFromArray (message.getData(), (int) message.getSize()))
                return;

            ProofMessage event;
            event.set_schema_version (command.schema_version());
            event.set_payload ("corytm-transport-proof-event");

            std::string serializedEvent;

            if (! event.SerializeToString (&serializedEvent))
                return;

            if (! sendMessage (juce::MemoryBlock (serializedEvent.data(), serializedEvent.size())))
                return;

            const std::lock_guard<std::mutex> lock (mutex);
            roundTripSucceeded = true;
            conditionVariable.notify_all();
        }

        std::string secret;
        std::mutex mutex;
        std::condition_variable conditionVariable;
        bool roundTripSucceeded = false;
        bool connectionWasLost = false;
    };
}

int main (int argc, char* argv[])
{
    if (argc != 3)
    {
        std::cerr << "usage: transport_proof <port> <secret>" << std::endl;
        return 1;
    }

    const juce::ScopedJuceInitialiser_GUI initialiser;

    const int port = std::atoi (argv[1]);
    TransportProofConnection connection (argv[2]);

    if (! connection.connectToSocket ("127.0.0.1", port, connectTimeoutMs))
    {
        std::cerr << "transport_proof: failed to connect to 127.0.0.1:" << port << std::endl;
        return 1;
    }

    if (! connection.waitForRoundTrip (roundTripTimeoutMs))
    {
        std::cerr << "transport_proof: round trip did not complete in time" << std::endl;
        return 1;
    }

    return 0;
}
