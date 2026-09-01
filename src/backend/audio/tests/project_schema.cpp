#include "project.pb.h"

#include <string>

using corytm::schemas::project::AudioClip;
using corytm::schemas::project::AudioTrack;
using corytm::schemas::project::MaterializeProjectCommand;
using corytm::schemas::project::ProjectRenderedEvent;

int main()
{
    MaterializeProjectCommand original;
    original.set_schema_version (1);
    original.mutable_project()->set_schema_version (1);
    original.mutable_project()->set_id ("corytm-project-schema-proof");

    AudioTrack* track = original.mutable_project()->add_tracks();
    track->set_schema_version (1);
    track->set_id ("track-1");

    AudioClip* clip = track->add_clips();
    clip->set_schema_version (1);
    clip->set_id ("clip-1");
    clip->set_start_seconds (0.0);
    clip->set_duration_seconds (2.5);

    std::string serializedCommand;
    const bool commandSerializedOk = original.SerializeToString (&serializedCommand);

    MaterializeProjectCommand decodedCommand;
    const bool commandParsedOk = decodedCommand.ParseFromString (serializedCommand);

    const bool commandRoundTripOk = commandSerializedOk && commandParsedOk
                                     && decodedCommand.project().id() == "corytm-project-schema-proof"
                                     && decodedCommand.project().tracks_size() == 1
                                     && decodedCommand.project().tracks (0).clips_size() == 1
                                     && decodedCommand.project().tracks (0).clips (0).id() == "clip-1"
                                     && decodedCommand.project().tracks (0).clips (0).duration_seconds() == 2.5;

    ProjectRenderedEvent originalEvent;
    originalEvent.set_schema_version (1);
    originalEvent.set_project_id ("corytm-project-schema-proof");
    originalEvent.set_rendered_file_path ("/tmp/corytm-project-schema-proof.wav");
    originalEvent.set_rendered_sample_count (110250);
    originalEvent.set_peak_amplitude (0.5);

    std::string serializedEvent;
    const bool eventSerializedOk = originalEvent.SerializeToString (&serializedEvent);

    ProjectRenderedEvent decodedEvent;
    const bool eventParsedOk = decodedEvent.ParseFromString (serializedEvent);

    const bool eventRoundTripOk = eventSerializedOk && eventParsedOk
                                  && decodedEvent.project_id() == originalEvent.project_id()
                                  && decodedEvent.rendered_file_path() == originalEvent.rendered_file_path()
                                  && decodedEvent.rendered_sample_count() == originalEvent.rendered_sample_count()
                                  && decodedEvent.peak_amplitude() == originalEvent.peak_amplitude();

    return commandRoundTripOk && eventRoundTripOk ? 0 : 1;
}
