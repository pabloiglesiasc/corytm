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

    using DecodedCommand = std::variant<ProjectSpec, MoveClipSpec>;

    std::optional<DecodedCommand> decodeCommand (const std::vector<std::byte>& commandBytes);

    std::vector<std::byte> encodeProjectRenderedEvent (const std::string& projectId, const RenderResult& result);

    std::vector<std::byte> encodeClipMovedEvent (const std::string& projectId, const std::string& trackId, const std::string& clipId,
                                                  double newStartSeconds, bool moved, const RenderResult& renderResult);
}
