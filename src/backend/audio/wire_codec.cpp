#include "wire_codec.h"

#include "project.pb.h"

using corytm::schemas::project::AudioClip;
using corytm::schemas::project::AudioTrack;
using corytm::schemas::project::MaterializeProjectCommand;
using corytm::schemas::project::ProjectRenderedEvent;

namespace corytm::native_runtime
{
    ProjectSpec decodeMaterializeCommand (const std::vector<std::byte>& commandBytes)
    {
        MaterializeProjectCommand command;

        if (! command.ParseFromArray (commandBytes.data(), (int) commandBytes.size()))
            return {};

        ProjectSpec project;
        project.id = command.project().id();

        for (const AudioTrack& trackMessage : command.project().tracks())
        {
            TrackSpec track;
            track.id = trackMessage.id();

            for (const AudioClip& clipMessage : trackMessage.clips())
            {
                track.clips.push_back ({ clipMessage.id(), clipMessage.start_seconds(), clipMessage.duration_seconds() });
            }

            project.tracks.push_back (std::move (track));
        }

        return project;
    }

    std::vector<std::byte> encodeRenderedEvent (const std::string& projectId, const RenderResult& result)
    {
        ProjectRenderedEvent event;
        event.set_schema_version (1);
        event.set_project_id (projectId);
        event.set_rendered_file_path (result.outputPath);
        event.set_rendered_sample_count (result.sampleCount);
        event.set_peak_amplitude (result.peakAmplitude);

        const std::string serialized = event.SerializeAsString();

        return { reinterpret_cast<const std::byte*> (serialized.data()),
                reinterpret_cast<const std::byte*> (serialized.data()) + serialized.size() };
    }
}
