#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace corytm::native_runtime
{
    struct ClipSpec
    {
        std::string id;
        double startSeconds;
        double durationSeconds;
    };

    struct TrackSpec
    {
        std::string id;
        std::vector<ClipSpec> clips;
    };

    struct ProjectSpec
    {
        std::string id;
        std::vector<TrackSpec> tracks;
    };

    struct RenderResult
    {
        bool success;
        std::string outputPath;
        std::uint64_t sampleCount;
        double peakAmplitude;
    };
}
