#include "materializer.h"
#include "wire_codec.h"

#include <juce_events/juce_events.h>

#include <condition_variable>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>

using namespace tracktion;
using corytm::native_runtime::decodeMaterializeCommand;
using corytm::native_runtime::encodeRenderedEvent;
using corytm::native_runtime::materialize;
using corytm::native_runtime::ProjectSpec;
using corytm::native_runtime::RenderResult;

namespace
{
    constexpr juce::uint32 transportMagicNumber = 0x636f7274;
    constexpr int connectTimeoutMs = 5000;
    constexpr int commandTimeoutMs = 5000;

    struct HeadlessUIBehaviour : public UIBehaviour
    {
    };

    struct HeadlessEngineBehaviour : public EngineBehaviour
    {
        bool autoInitialiseDeviceManager() override { return false; }
        int getNumberOfCPUsToUseForAudio() override { return 1; }
    };

    struct HeadlessPropertyStorage : public PropertyStorage
    {
        explicit HeadlessPropertyStorage (juce::StringRef appName) : PropertyStorage (appName) {}

        void removeProperty (SettingID) override {}
        juce::var getProperty (SettingID, const juce::var& defaultValue) override { return defaultValue; }
        void setProperty (SettingID, const juce::var&) override {}
        std::unique_ptr<juce::XmlElement> getXmlProperty (SettingID) override { return {}; }
        void setXmlProperty (SettingID, const juce::XmlElement&) override {}

        void removePropertyItem (SettingID, juce::StringRef) override {}
        juce::var getPropertyItem (SettingID, juce::StringRef, const juce::var& defaultValue) override { return defaultValue; }
        void setPropertyItem (SettingID, juce::StringRef, const juce::var&) override {}
        std::unique_ptr<juce::XmlElement> getXmlPropertyItem (SettingID, juce::StringRef) override { return {}; }
        void setXmlPropertyItem (SettingID, juce::StringRef, const juce::XmlElement&) override {}
    };

    class NativeRuntimeConnection final : public juce::InterprocessConnection
    {
    public:
        explicit NativeRuntimeConnection (std::string secretToSend)
            : juce::InterprocessConnection (false, transportMagicNumber),
              secret (std::move (secretToSend))
        {
        }

        ~NativeRuntimeConnection() override { disconnect(); }

        bool waitForCommand (int timeoutMs, std::vector<std::byte>& commandBytesOut)
        {
            std::unique_lock<std::mutex> lock (mutex);
            const bool arrived = conditionVariable.wait_for (lock, std::chrono::milliseconds (timeoutMs), [this]
            {
                return commandReceived || connectionWasLost;
            }) && commandReceived;

            if (arrived)
                commandBytesOut = std::move (receivedCommandBytes);

            return arrived;
        }

        void sendEvent (const std::vector<std::byte>& eventBytes)
        {
            sendMessage (juce::MemoryBlock (eventBytes.data(), eventBytes.size()));
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
            const auto* data = static_cast<const std::byte*> (message.getData());

            const std::lock_guard<std::mutex> lock (mutex);
            receivedCommandBytes.assign (data, data + message.getSize());
            commandReceived = true;
            conditionVariable.notify_all();
        }

        std::string secret;
        std::mutex mutex;
        std::condition_variable conditionVariable;
        std::vector<std::byte> receivedCommandBytes;
        bool commandReceived = false;
        bool connectionWasLost = false;
    };
}

int main (int argc, char* argv[])
{
    if (argc != 4)
    {
        std::cerr << "usage: native_runtime <port> <secret> <output_directory>" << std::endl;
        return 1;
    }

    const juce::ScopedJuceInitialiser_GUI initialiser;

    Engine engine { std::make_unique<HeadlessPropertyStorage> ("corytm-native-runtime"),
                    std::make_unique<HeadlessUIBehaviour>(),
                    std::make_unique<HeadlessEngineBehaviour>() };

    const int port = std::atoi (argv[1]);
    const juce::File outputDirectory { juce::String (argv[3]) };

    NativeRuntimeConnection connection (argv[2]);

    if (! connection.connectToSocket ("127.0.0.1", port, connectTimeoutMs))
    {
        std::cerr << "native_runtime: failed to connect to 127.0.0.1:" << port << std::endl;
        return 1;
    }

    std::vector<std::byte> commandBytes;

    if (! connection.waitForCommand (commandTimeoutMs, commandBytes))
    {
        std::cerr << "native_runtime: command did not arrive in time" << std::endl;
        return 1;
    }

    const ProjectSpec project = decodeMaterializeCommand (commandBytes);
    const RenderResult result = materialize (engine, project, outputDirectory);

    connection.sendEvent (encodeRenderedEvent (project.id, result));

    return result.success ? 0 : 1;
}
