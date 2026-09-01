#pragma once

#include "project_spec.h"

#include <tracktion_engine/tracktion_engine.h>

namespace corytm::native_runtime
{
    RenderResult materialize (tracktion::Engine& engine, const ProjectSpec& project, const juce::File& outputDirectory);
}
