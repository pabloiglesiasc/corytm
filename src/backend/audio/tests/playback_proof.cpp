#include "materializer.h"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_events/juce_events.h>

#include <iostream>
#include <memory>

using namespace tracktion;
using corytm::native_runtime::buildEdit;
using corytm::native_runtime::ClipSpec;
using corytm::native_runtime::getPlaybackPositionSeconds;
using corytm::native_runtime::isPlaying;
using corytm::native_runtime::openRealtimeOutputDevice;
using corytm::native_runtime::ProjectSpec;
using corytm::native_runtime::startPlayback;
using corytm::native_runtime::stopPlayback;
using corytm::native_runtime::TrackSpec;

namespace
{
    struct RealtimeUIBehaviour : public UIBehaviour
    {
    };

    struct RealtimeEngineBehaviour : public EngineBehaviour
    {
        bool autoInitialiseDeviceManager() override { return false; }
        bool shouldOpenAudioInputByDefault() override { return false; }
    };

    struct RealtimePropertyStorage : public PropertyStorage
    {
        explicit RealtimePropertyStorage (juce::StringRef appName) : PropertyStorage (appName) {}

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

    void pumpMessageLoop (int milliseconds)
    {
        const juce::uint32 deadline = juce::Time::getMillisecondCounter() + (juce::uint32) milliseconds;

        while (juce::Time::getMillisecondCounter() < deadline)
            juce::MessageManager::getInstance()->runDispatchLoopUntil (10);
    }
}

int main()
{
    const juce::ScopedJuceInitialiser_GUI initialiser;

    Engine engine { std::make_unique<RealtimePropertyStorage> ("corytm-playback-proof"),
                    std::make_unique<RealtimeUIBehaviour>(),
                    std::make_unique<RealtimeEngineBehaviour>() };

    if (! openRealtimeOutputDevice (engine))
    {
        std::cout << "playback_proof: no real audio output device available in this environment; "
                      "skipping the real-time assertions (expected on some CI runners)"
                   << std::endl;
        return 0;
    }

    const ProjectSpec project { "playback-proof-project",
                                { TrackSpec { "track-1", { ClipSpec { "clip-1", 0.0, 3.0 } } } } };

    auto edit = buildEdit (engine, project, Edit::EditRole::forEditing);

    startPlayback (*edit);
    pumpMessageLoop (50);

    const bool startedPlaying = isPlaying (*edit);
    const double positionAfterStart = getPlaybackPositionSeconds (*edit);

    pumpMessageLoop (500);

    const double positionAfterWait = getPlaybackPositionSeconds (*edit);
    const bool positionAdvanced = (positionAfterWait - positionAfterStart) > 0.2;

    stopPlayback (*edit);
    pumpMessageLoop (50);

    const bool stoppedPlaying = ! isPlaying (*edit);

    if (! startedPlaying || ! positionAdvanced || ! stoppedPlaying)
    {
        std::cerr << "playback_proof: FAILED (startedPlaying=" << (startedPlaying ? "true" : "false")
                   << " positionAdvanced=" << (positionAdvanced ? "true" : "false")
                   << " [" << positionAfterStart << " -> " << positionAfterWait << "]"
                   << " stoppedPlaying=" << (stoppedPlaying ? "true" : "false") << ")" << std::endl;
        return 1;
    }

    std::cout << "playback_proof: real-time playback started, advanced ("
              << positionAfterStart << "s -> " << positionAfterWait << "s), and stopped correctly" << std::endl;

    return 0;
}
