#include "headless_engine.h"
#include "materializer.h"

#include <cmath>
#include <memory>

using namespace tracktion;
using corytm::native_runtime::ClipSpec;
using corytm::native_runtime::materialize;
using corytm::native_runtime::ProjectSpec;
using corytm::native_runtime::RenderResult;
using corytm::native_runtime::TrackSpec;
using corytm::native_runtime::test::makeDeterministicHeadlessEngine;

namespace
{
    bool nearlyEqual (double a, double b, double tolerance)
    {
        return std::abs (a - b) <= tolerance;
    }
}

int main()
{
    const juce::ScopedJuceInitialiser_GUI initialiser;

    auto engine = makeDeterministicHeadlessEngine ("corytm-materializer-proof");

    const ProjectSpec project { "materializer-proof-project",
                                { TrackSpec { "track-1", { ClipSpec { "clip-1", 0.0, 2.0 } } } } };

    const juce::File outputDirectory = engine->getTemporaryFileManager().getTempDirectory();

    const RenderResult first = materialize (*engine, project, outputDirectory);
    const RenderResult second = materialize (*engine, project, outputDirectory);

    const bool firstOk = first.success
                          && nearlyEqual ((double) first.sampleCount / 44100.0, 2.0, 0.01)
                          && first.peakAmplitude > 0.5;

    const bool secondOk = second.success
                           && second.sampleCount == first.sampleCount
                           && nearlyEqual (second.peakAmplitude, first.peakAmplitude, 0.0001);

    return firstOk && secondOk ? 0 : 1;
}
