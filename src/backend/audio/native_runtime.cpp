#include "materializer.h"
#include "wire_codec.h"

#include <juce_events/juce_events.h>

#include <condition_variable>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <variant>

using namespace tracktion;
using corytm::native_runtime::buildEdit;
using corytm::native_runtime::decodeCommand;
using corytm::native_runtime::encodeClipMovedEvent;
using corytm::native_runtime::encodeDevicePreparedEvent;
using corytm::native_runtime::encodePlaybackPositionEvent;
using corytm::native_runtime::encodePlaybackStartedEvent;
using corytm::native_runtime::encodePlaybackStoppedEvent;
using corytm::native_runtime::encodeProjectRenderedEvent;
using corytm::native_runtime::getEditEndSeconds;
using corytm::native_runtime::getPlaybackPositionSeconds;
using corytm::native_runtime::isPlaying;
using corytm::native_runtime::moveClip;
using corytm::native_runtime::MoveClipSpec;
using corytm::native_runtime::GetPlaybackPositionSpec;
using corytm::native_runtime::openRealtimeOutputDevice;
using corytm::native_runtime::PlaySpec;
using corytm::native_runtime::PrepareDeviceSpec;
using corytm::native_runtime::ProjectSpec;
using corytm::native_runtime::renderEdit;
using corytm::native_runtime::RenderResult;
using corytm::native_runtime::startPlayback;
using corytm::native_runtime::StopSpec;
using corytm::native_runtime::stopPlayback;

namespace
{
    constexpr juce::uint32 transportMagicNumber = 0x636f7274;
    constexpr int connectTimeoutMs = 5000;
    constexpr int firstCommandTimeoutMs = 5000;
    constexpr int subsequentCommandTimeoutMs = 24 * 60 * 60 * 1000;
    constexpr int playbackPollSliceMs = 10;

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
            {
                commandBytesOut = std::move (receivedCommandBytes);
                commandReceived = false;
            }

            return arrived;
        }

        void sendEvent (const std::vector<std::byte>& eventBytes)
        {
            sendMessage (juce::MemoryBlock (eventBytes.data(), eventBytes.size()));
        }

        bool wasConnectionLost() const
        {
            const std::lock_guard<std::mutex> lock (mutex);
            return connectionWasLost;
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
        mutable std::mutex mutex;
        std::condition_variable conditionVariable;
        std::vector<std::byte> receivedCommandBytes;
        bool commandReceived = false;
        bool connectionWasLost = false;
    };

    bool waitForNextCommand (NativeRuntimeConnection& connection, Edit* liveEdit, bool hasReceivedAnyCommand, std::vector<std::byte>& commandBytesOut)
    {
        while (liveEdit != nullptr && isPlaying (*liveEdit))
        {
            if (connection.waitForCommand (playbackPollSliceMs, commandBytesOut))
                return true;

            if (connection.wasConnectionLost())
                return false;

            juce::MessageManager::getInstance()->runDispatchLoopUntil (playbackPollSliceMs);

            const double editEndSeconds = getEditEndSeconds (*liveEdit);

            if (editEndSeconds > 0.0 && getPlaybackPositionSeconds (*liveEdit) >= editEndSeconds)
            {
                stopPlayback (*liveEdit);
                break;
            }
        }

        return connection.waitForCommand (hasReceivedAnyCommand ? subsequentCommandTimeoutMs : firstCommandTimeoutMs, commandBytesOut);
    }
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

    std::unique_ptr<Edit> liveEdit;
    std::string liveProjectId;
    double lastStoppedPositionSeconds = 0.0;
    bool sessionSucceeded = true;
    bool hasReceivedAnyCommand = false;
    std::vector<std::byte> commandBytes;

    while (waitForNextCommand (connection, liveEdit.get(), hasReceivedAnyCommand, commandBytes))
    {
        hasReceivedAnyCommand = true;

        const auto decoded = decodeCommand (commandBytes);

        if (! decoded)
        {
            std::cerr << "native_runtime: received an unrecognised command" << std::endl;
            return 1;
        }

        if (const auto* project = std::get_if<ProjectSpec> (&*decoded))
        {
            liveProjectId = project->id;
            liveEdit = buildEdit (engine, *project);

            const RenderResult result = renderEdit (engine, *liveEdit, liveProjectId, outputDirectory);
            sessionSucceeded = sessionSucceeded && result.success;

            connection.sendEvent (encodeProjectRenderedEvent (liveProjectId, result));
        }
        else if (const auto* move = std::get_if<MoveClipSpec> (&*decoded))
        {
            RenderResult renderResult { false, {}, 0, 0.0 };
            const bool moved = liveEdit != nullptr && moveClip (*liveEdit, move->trackId, move->clipId, move->newStartSeconds);

            if (moved)
            {
                renderResult = renderEdit (engine, *liveEdit, liveProjectId, outputDirectory);
                sessionSucceeded = sessionSucceeded && renderResult.success;
            }

            connection.sendEvent (encodeClipMovedEvent (move->projectId, move->trackId, move->clipId, move->newStartSeconds, moved, renderResult));
        }
        else if (const auto* play = std::get_if<PlaySpec> (&*decoded))
        {
            const bool resumingSameProject = (liveProjectId == play->project.id) && lastStoppedPositionSeconds > 0.0;
            const double resumePositionSeconds = lastStoppedPositionSeconds;
            lastStoppedPositionSeconds = 0.0;

            liveProjectId = play->project.id;
            liveEdit = buildEdit (engine, play->project, Edit::EditRole::forEditing);

            if (resumingSameProject)
                liveEdit->getTransport().setPosition (TimePosition::fromSeconds (resumePositionSeconds));

            const bool deviceOpened = openRealtimeOutputDevice (engine);

            if (deviceOpened)
                startPlayback (*liveEdit);

            connection.sendEvent (encodePlaybackStartedEvent (liveProjectId, deviceOpened));
        }
        else if (std::get_if<GetPlaybackPositionSpec> (&*decoded) != nullptr)
        {
            const bool playing = liveEdit != nullptr && isPlaying (*liveEdit);
            const double position = liveEdit != nullptr ? getPlaybackPositionSeconds (*liveEdit) : 0.0;

            connection.sendEvent (encodePlaybackPositionEvent (playing, position));
        }
        else if (std::get_if<StopSpec> (&*decoded) != nullptr)
        {
            const double finalPosition = liveEdit != nullptr ? getPlaybackPositionSeconds (*liveEdit) : 0.0;

            if (liveEdit != nullptr)
                stopPlayback (*liveEdit);

            lastStoppedPositionSeconds = finalPosition;

            connection.sendEvent (encodePlaybackStoppedEvent (liveProjectId, finalPosition));
        }
        else if (std::get_if<PrepareDeviceSpec> (&*decoded) != nullptr)
        {
            const bool deviceOpened = openRealtimeOutputDevice (engine);

            connection.sendEvent (encodeDevicePreparedEvent (deviceOpened));
        }
    }

    if (! connection.wasConnectionLost())
    {
        std::cerr << "native_runtime: command did not arrive in time" << std::endl;
        return 1;
    }

    return sessionSucceeded ? 0 : 1;
}
