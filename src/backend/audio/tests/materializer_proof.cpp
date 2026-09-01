#include "materializer.h"

#include <cmath>
#include <memory>

using namespace tracktion;
using corytm::native_runtime::ClipSpec;
using corytm::native_runtime::materialize;
using corytm::native_runtime::ProjectSpec;
using corytm::native_runtime::RenderResult;
using corytm::native_runtime::TrackSpec;

namespace
{
    struct ProofUIBehaviour : public UIBehaviour
    {
    };

    struct ProofEngineBehaviour : public EngineBehaviour
    {
        bool autoInitialiseDeviceManager() override { return false; }
        int getNumberOfCPUsToUseForAudio() override { return 1; }
    };

    struct ProofPropertyStorage : public PropertyStorage
    {
        explicit ProofPropertyStorage (juce::StringRef appName) : PropertyStorage (appName) {}

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

    bool nearlyEqual (double a, double b, double tolerance)
    {
        return std::abs (a - b) <= tolerance;
    }
}

int main()
{
    const juce::ScopedJuceInitialiser_GUI initialiser;

    Engine engine { std::make_unique<ProofPropertyStorage> ("corytm-materializer-proof"),
                    std::make_unique<ProofUIBehaviour>(),
                    std::make_unique<ProofEngineBehaviour>() };

    const ProjectSpec project { "materializer-proof-project",
                                { TrackSpec { "track-1", { ClipSpec { "clip-1", 0.0, 2.0 } } } } };

    const juce::File outputDirectory = engine.getTemporaryFileManager().getTempDirectory();

    const RenderResult first = materialize (engine, project, outputDirectory);
    const RenderResult second = materialize (engine, project, outputDirectory);

    const bool firstOk = first.success
                          && nearlyEqual ((double) first.sampleCount / 44100.0, 2.0, 0.01)
                          && first.peakAmplitude > 0.5;

    const bool secondOk = second.success
                           && second.sampleCount == first.sampleCount
                           && nearlyEqual (second.peakAmplitude, first.peakAmplitude, 0.0001);

    return firstOk && secondOk ? 0 : 1;
}
