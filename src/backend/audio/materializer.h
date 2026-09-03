#pragma once

#include "project_spec.h"

#include <tracktion_engine/tracktion_engine.h>

#include <memory>
#include <string>

namespace corytm::native_runtime
{
    std::unique_ptr<tracktion::Edit> buildEdit (tracktion::Engine& engine, const ProjectSpec& project,
                                                 tracktion::Edit::EditRole role = tracktion::Edit::EditRole::forRendering);

    bool moveClip (tracktion::Edit& edit, const std::string& trackId, const std::string& clipId, double newStartSeconds);

    RenderResult renderEdit (tracktion::Engine& engine, tracktion::Edit& edit, const std::string& projectId, const juce::File& outputDirectory);

    RenderResult materialize (tracktion::Engine& engine, const ProjectSpec& project, const juce::File& outputDirectory);

    // The position, in seconds, where `edit`'s last clip ends — the
    // mechanical length of its already-materialized content, not a
    // musical/arrangement interpretation. Shared by `renderEdit` (an
    // offline render needs exactly this long) and real-time playback's
    // own effective-end-of-content stop (see `native_runtime.cpp`).
    double getEditEndSeconds (tracktion::Edit& edit);

    // Opens a real audio output device via `DeviceManager`, blocking
    // until it settles. Idempotent: a second call against an
    // already-open, already-settled device returns `true` immediately
    // without re-triggering `DeviceManager::initialise()`'s async
    // rescans — callers may call this speculatively ahead of `Play`
    // (to pay its cost before the user is waiting on it) and again
    // from `Play` itself as a defensive fallback, at negligible cost
    // once already warm.
    bool openRealtimeOutputDevice (tracktion::Engine& engine);

    void startPlayback (tracktion::Edit& edit);

    void stopPlayback (tracktion::Edit& edit);

    bool isPlaying (const tracktion::Edit& edit);

    double getPlaybackPositionSeconds (const tracktion::Edit& edit);
}
