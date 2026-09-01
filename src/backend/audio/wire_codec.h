#pragma once

#include "project_spec.h"

#include <cstddef>
#include <string>
#include <vector>

namespace corytm::native_runtime
{
    ProjectSpec decodeMaterializeCommand (const std::vector<std::byte>& commandBytes);

    std::vector<std::byte> encodeRenderedEvent (const std::string& projectId, const RenderResult& result);
}
