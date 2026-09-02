#include "materializer.h"

#include <juce_audio_formats/juce_audio_formats.h>

#include <atomic>
#include <cmath>

using namespace tracktion;

namespace corytm::native_runtime
{
    namespace
    {
        constexpr double fixtureFrequencyHz = 440.0;
        constexpr double fixtureSampleRate = 44100.0;
        constexpr int renderTimeoutMs = 10000;

        juce::File generateSineFixture (Engine& engine, double durationSeconds)
        {
            const int numFrames = (int) std::ceil (fixtureSampleRate * durationSeconds);
            juce::AudioBuffer<float> buffer (1, numFrames);
            float* channel = buffer.getWritePointer (0);

            for (int frame = 0; frame < numFrames; ++frame)
                channel[frame] = (float) std::sin (2.0 * juce::MathConstants<double>::pi * fixtureFrequencyHz * (double) frame / fixtureSampleRate);

            const juce::File fixtureFile = engine.getTemporaryFileManager()
                                              .getTempFile (juce::Uuid().toString() + ".wav")
                                              .getNonexistentSibling();
            juce::WavAudioFormat format;

            if (auto writer = std::unique_ptr<juce::AudioFormatWriter> (
                    format.createWriterFor (fixtureFile.createOutputStream().release(), fixtureSampleRate, 1, 16, {}, 0)))
            {
                writer->writeFromAudioSampleBuffer (buffer, 0, numFrames);
            }

            return fixtureFile;
        }
    }

    std::unique_ptr<Edit> buildEdit (Engine& engine, const ProjectSpec& project)
    {
        auto edit = Edit::createSingleTrackEdit (engine, Edit::EditRole::forRendering);

        if (project.tracks.empty())
            return edit;

        auto audioTracks = getAudioTracks (*edit);

        if (audioTracks.isEmpty())
            return edit;

        AudioTrack* track = audioTracks[0];
        track->setName (juce::String (project.tracks[0].id));

        for (const ClipSpec& clipSpec : project.tracks[0].clips)
        {
            const juce::File fixtureFile = generateSineFixture (engine, clipSpec.durationSeconds);
            const double clipEndSeconds = clipSpec.startSeconds + clipSpec.durationSeconds;

            insertWaveClip (*track, juce::String (clipSpec.id), fixtureFile,
                            { TimeRange { TimePosition::fromSeconds (clipSpec.startSeconds),
                                         TimePosition::fromSeconds (clipEndSeconds) } },
                            DeleteExistingClips::no);
        }

        return edit;
    }

    bool moveClip (Edit& edit, const std::string& trackId, const std::string& clipId, double newStartSeconds)
    {
        const juce::String targetTrackId (trackId);
        const juce::String targetClipId (clipId);

        for (AudioTrack* track : getAudioTracks (edit))
        {
            if (track->getName() != targetTrackId)
                continue;

            for (Clip* clip : track->getClips())
            {
                if (clip->getName() != targetClipId)
                    continue;

                clip->setStart (TimePosition::fromSeconds (newStartSeconds), false, true);
                return true;
            }
        }

        return false;
    }

    RenderResult renderEdit (Engine& engine, Edit& edit, const std::string& projectId, const juce::File& outputDirectory)
    {
        double editEndSeconds = 0.0;

        for (AudioTrack* track : getAudioTracks (edit))
            for (Clip* clip : track->getClips())
                editEndSeconds = juce::jmax (editEndSeconds, clip->getPosition().getEnd().inSeconds());

        if (editEndSeconds <= 0.0)
            return { false, {}, 0, 0.0 };

        const juce::File destFile = outputDirectory.getChildFile (juce::String (projectId) + ".wav").getNonexistentSibling();

        Renderer::Parameters params (edit);
        params.destFile = destFile;
        params.time = TimeRange { TimePosition::fromSeconds (0.0), TimePosition::fromSeconds (editEndSeconds) };
        params.audioFormat = engine.getAudioFileFormatManager().getWavFormat();

        std::atomic<bool> renderFinished { false };
        std::atomic<bool> renderSucceeded { false };

        auto handle = EditRenderer::render (std::move (params), [&] (tl::expected<juce::File, std::string> result)
        {
            renderSucceeded = result.has_value();
            renderFinished = true;
        });

        const juce::uint32 deadline = juce::Time::getMillisecondCounter() + (juce::uint32) renderTimeoutMs;

        while (! renderFinished && juce::Time::getMillisecondCounter() < deadline)
            juce::MessageManager::getInstance()->runDispatchLoopUntil (10);

        const bool completedInTime = renderFinished.load();

        if (! completedInTime || ! renderSucceeded || ! destFile.existsAsFile())
            return { false, {}, 0, 0.0 };

        std::unique_ptr<juce::AudioFormatReader> reader (engine.getAudioFileFormatManager().readFormatManager.createReaderFor (destFile));

        if (reader == nullptr)
            return { false, {}, 0, 0.0 };

        float lowestLeft = 0.0f;
        float highestLeft = 0.0f;
        float lowestRight = 0.0f;
        float highestRight = 0.0f;
        reader->readMaxLevels (0, reader->lengthInSamples, lowestLeft, highestLeft, lowestRight, highestRight);

        const double peakAmplitude = juce::jmax (std::abs (lowestLeft), std::abs (highestLeft));

        return { true, destFile.getFullPathName().toStdString(), (std::uint64_t) reader->lengthInSamples, peakAmplitude };
    }

    RenderResult materialize (Engine& engine, const ProjectSpec& project, const juce::File& outputDirectory)
    {
        if (project.tracks.empty() || project.tracks[0].clips.empty())
            return { false, {}, 0, 0.0 };

        auto edit = buildEdit (engine, project);

        return renderEdit (engine, *edit, project.id, outputDirectory);
    }
}
