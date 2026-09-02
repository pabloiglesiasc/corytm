#include "headless_engine.h"
#include "materializer.h"

#include <juce_audio_formats/juce_audio_formats.h>

#include <cmath>
#include <memory>

using namespace tracktion;
using corytm::native_runtime::buildEdit;
using corytm::native_runtime::ClipSpec;
using corytm::native_runtime::moveClip;
using corytm::native_runtime::ProjectSpec;
using corytm::native_runtime::renderEdit;
using corytm::native_runtime::RenderResult;
using corytm::native_runtime::TrackSpec;
using corytm::native_runtime::test::makeDeterministicHeadlessEngine;

namespace
{
    constexpr double sampleRate = 44100.0;

    bool nearlyEqual (double a, double b, double tolerance)
    {
        return std::abs (a - b) <= tolerance;
    }

    double peakAmplitudeInRange (Engine& engine, const std::string& filePath, juce::int64 startSample, juce::int64 numSamples)
    {
        if (numSamples <= 0)
            return 0.0;

        std::unique_ptr<juce::AudioFormatReader> reader (
            engine.getAudioFileFormatManager().readFormatManager.createReaderFor (juce::File (filePath)));

        if (reader == nullptr)
            return 1.0;

        float lowestLeft = 0.0f, highestLeft = 0.0f, lowestRight = 0.0f, highestRight = 0.0f;
        reader->readMaxLevels (startSample, numSamples, lowestLeft, highestLeft, lowestRight, highestRight);

        return juce::jmax (std::abs (lowestLeft), std::abs (highestLeft));
    }
}

int main()
{
    const juce::ScopedJuceInitialiser_GUI initialiser;

    auto engine = makeDeterministicHeadlessEngine ("corytm-live-session-proof");
    const juce::File outputDirectory = engine->getTemporaryFileManager().getTempDirectory();

    const ProjectSpec project { "live-session-proof-project",
                                { TrackSpec { "track-1", { ClipSpec { "clip-1", 0.0, 1.0 } } } } };

    auto edit = buildEdit (*engine, project);

    const RenderResult baseline = renderEdit (*engine, *edit, project.id, outputDirectory);

    const bool baselineOk = baseline.success
                             && nearlyEqual ((double) baseline.sampleCount / sampleRate, 1.0, 0.01)
                             && baseline.peakAmplitude > 0.5;

    const bool moveSucceeded = moveClip (*edit, "track-1", "clip-1", 2.0);
    const RenderResult afterMove = renderEdit (*engine, *edit, project.id, outputDirectory);

    const auto newStartSample = (juce::int64) std::llround (2.0 * sampleRate);
    const double silenceBeforeMove = afterMove.success
        ? peakAmplitudeInRange (*engine, afterMove.outputPath, 0, newStartSample)
        : 1.0;
    const double signalAfterMove = afterMove.success
        ? peakAmplitudeInRange (*engine, afterMove.outputPath, newStartSample, (juce::int64) afterMove.sampleCount - newStartSample)
        : 0.0;

    const bool moveOk = moveSucceeded
                         && afterMove.success
                         && nearlyEqual ((double) afterMove.sampleCount / sampleRate, 3.0, 0.01)
                         && silenceBeforeMove < 0.01
                         && signalAfterMove > 0.5;

    const bool moveRejectsUnknownIds = ! moveClip (*edit, "track-1", "no-such-clip", 0.0)
                                        && ! moveClip (*edit, "no-such-track", "clip-1", 0.0);

    const RenderResult afterRejectedMoves = renderEdit (*engine, *edit, project.id, outputDirectory);

    const bool unchangedAfterRejectedMoves = afterRejectedMoves.success
        && afterRejectedMoves.sampleCount == afterMove.sampleCount
        && nearlyEqual (afterRejectedMoves.peakAmplitude, afterMove.peakAmplitude, 0.0001);

    return baselineOk && moveOk && moveRejectsUnknownIds && unchangedAfterRejectedMoves ? 0 : 1;
}
