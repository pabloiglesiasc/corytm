#include <tracktion_engine/tracktion_engine.h>

using namespace tracktion;

namespace
{
    struct ProofUIBehaviour : public UIBehaviour
    {
    };

    struct ProofEngineBehaviour : public EngineBehaviour
    {
        bool autoInitialiseDeviceManager() override { return false; }
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
}

int main()
{
    juce::ScopedJuceInitialiser_GUI initialiser;

    Engine engine { std::make_unique<ProofPropertyStorage> ("corytm-toolchain-proof"),
                    std::make_unique<ProofUIBehaviour>(),
                    std::make_unique<ProofEngineBehaviour>() };

    return engine.getTemporaryFileManager().getTempDirectory().exists() ? 0 : 1;
}
