#pragma once

#include <tracktion_engine/tracktion_engine.h>

#include <memory>

namespace corytm::native_runtime::test
{
    inline std::unique_ptr<tracktion::Engine> makeDeterministicHeadlessEngine (juce::StringRef applicationName)
    {
        struct HeadlessUIBehaviour : public tracktion::UIBehaviour
        {
        };

        struct HeadlessEngineBehaviour : public tracktion::EngineBehaviour
        {
            bool autoInitialiseDeviceManager() override { return false; }
            int getNumberOfCPUsToUseForAudio() override { return 1; }
        };

        struct HeadlessPropertyStorage : public tracktion::PropertyStorage
        {
            explicit HeadlessPropertyStorage (juce::StringRef appName) : PropertyStorage (appName) {}

            void removeProperty (tracktion::SettingID) override {}
            juce::var getProperty (tracktion::SettingID, const juce::var& defaultValue) override { return defaultValue; }
            void setProperty (tracktion::SettingID, const juce::var&) override {}
            std::unique_ptr<juce::XmlElement> getXmlProperty (tracktion::SettingID) override { return {}; }
            void setXmlProperty (tracktion::SettingID, const juce::XmlElement&) override {}

            void removePropertyItem (tracktion::SettingID, juce::StringRef) override {}
            juce::var getPropertyItem (tracktion::SettingID, juce::StringRef, const juce::var& defaultValue) override { return defaultValue; }
            void setPropertyItem (tracktion::SettingID, juce::StringRef, const juce::var&) override {}
            std::unique_ptr<juce::XmlElement> getXmlPropertyItem (tracktion::SettingID, juce::StringRef) override { return {}; }
            void setXmlPropertyItem (tracktion::SettingID, juce::StringRef, const juce::XmlElement&) override {}
        };

        return std::make_unique<tracktion::Engine> (
            std::make_unique<HeadlessPropertyStorage> (applicationName),
            std::make_unique<HeadlessUIBehaviour>(),
            std::make_unique<HeadlessEngineBehaviour>());
    }
}
