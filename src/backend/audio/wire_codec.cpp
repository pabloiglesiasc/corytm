#include "wire_codec.h"

#include "project.pb.h"

using corytm::schemas::project::AudioClip;
using corytm::schemas::project::AudioTrack;
using corytm::schemas::project::ClipMovedEvent;
using corytm::schemas::project::Command;
using corytm::schemas::project::Event;
using corytm::schemas::project::ProjectRenderedEvent;

namespace corytm::native_runtime
{
    namespace
    {
        ProjectSpec toProjectSpec (const corytm::schemas::project::Project& projectMessage)
        {
            ProjectSpec project;
            project.id = projectMessage.id();

            for (const AudioTrack& trackMessage : projectMessage.tracks())
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

        std::vector<std::byte> toBytes (const std::string& serialized)
        {
            return { reinterpret_cast<const std::byte*> (serialized.data()),
                    reinterpret_cast<const std::byte*> (serialized.data()) + serialized.size() };
        }
    }

    std::optional<DecodedCommand> decodeCommand (const std::vector<std::byte>& commandBytes)
    {
        Command command;

        if (! command.ParseFromArray (commandBytes.data(), (int) commandBytes.size()))
            return std::nullopt;

        if (command.has_materialize())
            return DecodedCommand { toProjectSpec (command.materialize().project()) };

        if (command.has_move_clip())
        {
            const auto& moveClip = command.move_clip();
            return DecodedCommand { MoveClipSpec { moveClip.project_id(), moveClip.track_id(), moveClip.clip_id(), moveClip.new_start_seconds() } };
        }

        return std::nullopt;
    }

    std::vector<std::byte> encodeProjectRenderedEvent (const std::string& projectId, const RenderResult& result)
    {
        ProjectRenderedEvent renderedEvent;
        renderedEvent.set_schema_version (1);
        renderedEvent.set_project_id (projectId);
        renderedEvent.set_rendered_file_path (result.outputPath);
        renderedEvent.set_rendered_sample_count (result.sampleCount);
        renderedEvent.set_peak_amplitude (result.peakAmplitude);

        Event event;
        *event.mutable_project_rendered() = std::move (renderedEvent);

        return toBytes (event.SerializeAsString());
    }

    std::vector<std::byte> encodeClipMovedEvent (const std::string& projectId, const std::string& trackId, const std::string& clipId,
                                                  double newStartSeconds, bool moved, const RenderResult& renderResult)
    {
        ClipMovedEvent clipMovedEvent;
        clipMovedEvent.set_schema_version (1);
        clipMovedEvent.set_project_id (projectId);
        clipMovedEvent.set_track_id (trackId);
        clipMovedEvent.set_clip_id (clipId);
        clipMovedEvent.set_start_seconds (newStartSeconds);
        clipMovedEvent.set_moved (moved);
        clipMovedEvent.set_rendered_file_path (renderResult.outputPath);
        clipMovedEvent.set_rendered_sample_count (renderResult.sampleCount);
        clipMovedEvent.set_peak_amplitude (renderResult.peakAmplitude);

        Event event;
        *event.mutable_clip_moved() = std::move (clipMovedEvent);

        return toBytes (event.SerializeAsString());
    }
}
