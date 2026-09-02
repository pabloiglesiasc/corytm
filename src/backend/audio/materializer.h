#pragma once

#include "project_spec.h"

#include <tracktion_engine/tracktion_engine.h>

#include <memory>
#include <string>

namespace corytm::native_runtime
{
    std::unique_ptr<tracktion::Edit> buildEdit (tracktion::Engine& engine, const ProjectSpec& project);

    bool moveClip (tracktion::Edit& edit, const std::string& trackId, const std::string& clipId, double newStartSeconds);

    RenderResult renderEdit (tracktion::Engine& engine, tracktion::Edit& edit, const std::string& projectId, const juce::File& outputDirectory);

    RenderResult materialize (tracktion::Engine& engine, const ProjectSpec& project, const juce::File& outputDirectory);
}
