#pragma once

#include "project_spec.h"

#include <cstddef>
#include <optional>
#include <string>
#include <variant>
#include <vector>

namespace corytm::native_runtime
{
    struct MoveClipSpec
    {
        std::string projectId;
        std::string trackId;
        std::string clipId;
        double newStartSeconds;
    };

    struct PlaySpec
    {
        ProjectSpec project;
    };

    struct StopSpec
    {
    };

    struct GetPlaybackPositionSpec
    {
    };

    struct PrepareDeviceSpec
    {
    };

    using DecodedCommand = std::variant<ProjectSpec, MoveClipSpec, PlaySpec, StopSpec, GetPlaybackPositionSpec, PrepareDeviceSpec>;

    std::optional<DecodedCommand> decodeCommand (const std::vector<std::byte>& commandBytes);

    std::vector<std::byte> encodeProjectRenderedEvent (const std::string& projectId, const RenderResult& result);

    std::vector<std::byte> encodeClipMovedEvent (const std::string& projectId, const std::string& trackId, const std::string& clipId,
                                                  double newStartSeconds, bool moved, const RenderResult& renderResult);

    std::vector<std::byte> encodePlaybackStartedEvent (const std::string& projectId, bool deviceOpened);

    std::vector<std::byte> encodePlaybackStoppedEvent (const std::string& projectId, double finalPositionSeconds);

    std::vector<std::byte> encodePlaybackPositionEvent (bool isPlaying, double positionSeconds);

    std::vector<std::byte> encodeDevicePreparedEvent (bool deviceOpened);
}
