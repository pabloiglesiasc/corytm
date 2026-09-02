#include "project.pb.h"

#include <string>

using corytm::schemas::project::AudioClip;
using corytm::schemas::project::AudioTrack;
using corytm::schemas::project::ClipMovedEvent;
using corytm::schemas::project::Command;
using corytm::schemas::project::Event;
using corytm::schemas::project::MaterializeProjectCommand;
using corytm::schemas::project::MoveClipCommand;
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

    MoveClipCommand originalMoveCommand;
    originalMoveCommand.set_schema_version (1);
    originalMoveCommand.set_project_id ("corytm-project-schema-proof");
    originalMoveCommand.set_track_id ("track-1");
    originalMoveCommand.set_clip_id ("clip-1");
    originalMoveCommand.set_new_start_seconds (5.0);

    std::string serializedMoveCommand;
    const bool moveCommandSerializedOk = originalMoveCommand.SerializeToString (&serializedMoveCommand);

    MoveClipCommand decodedMoveCommand;
    const bool moveCommandParsedOk = decodedMoveCommand.ParseFromString (serializedMoveCommand);

    const bool moveCommandRoundTripOk = moveCommandSerializedOk && moveCommandParsedOk
                                        && decodedMoveCommand.project_id() == "corytm-project-schema-proof"
                                        && decodedMoveCommand.track_id() == "track-1"
                                        && decodedMoveCommand.clip_id() == "clip-1"
                                        && decodedMoveCommand.new_start_seconds() == 5.0;

    ClipMovedEvent originalMovedEvent;
    originalMovedEvent.set_schema_version (1);
    originalMovedEvent.set_project_id ("corytm-project-schema-proof");
    originalMovedEvent.set_track_id ("track-1");
    originalMovedEvent.set_clip_id ("clip-1");
    originalMovedEvent.set_start_seconds (5.0);
    originalMovedEvent.set_moved (true);
    originalMovedEvent.set_rendered_file_path ("/tmp/corytm-project-schema-proof-moved.wav");
    originalMovedEvent.set_rendered_sample_count (220500);
    originalMovedEvent.set_peak_amplitude (0.75);

    std::string serializedMovedEvent;
    const bool movedEventSerializedOk = originalMovedEvent.SerializeToString (&serializedMovedEvent);

    ClipMovedEvent decodedMovedEvent;
    const bool movedEventParsedOk = decodedMovedEvent.ParseFromString (serializedMovedEvent);

    const bool movedEventRoundTripOk = movedEventSerializedOk && movedEventParsedOk
                                       && decodedMovedEvent.project_id() == originalMovedEvent.project_id()
                                       && decodedMovedEvent.track_id() == originalMovedEvent.track_id()
                                       && decodedMovedEvent.clip_id() == originalMovedEvent.clip_id()
                                       && decodedMovedEvent.start_seconds() == originalMovedEvent.start_seconds()
                                       && decodedMovedEvent.moved() == originalMovedEvent.moved()
                                       && decodedMovedEvent.rendered_file_path() == originalMovedEvent.rendered_file_path()
                                       && decodedMovedEvent.rendered_sample_count() == originalMovedEvent.rendered_sample_count()
                                       && decodedMovedEvent.peak_amplitude() == originalMovedEvent.peak_amplitude();

    Command originalMaterializeCommandEnvelope;
    *originalMaterializeCommandEnvelope.mutable_materialize() = original;

    std::string serializedMaterializeEnvelope;
    const bool materializeEnvelopeSerializedOk = originalMaterializeCommandEnvelope.SerializeToString (&serializedMaterializeEnvelope);

    Command decodedMaterializeCommandEnvelope;
    const bool materializeEnvelopeParsedOk = decodedMaterializeCommandEnvelope.ParseFromString (serializedMaterializeEnvelope);

    const bool materializeEnvelopeRoundTripOk = materializeEnvelopeSerializedOk && materializeEnvelopeParsedOk
                                                && decodedMaterializeCommandEnvelope.has_materialize()
                                                && ! decodedMaterializeCommandEnvelope.has_move_clip()
                                                && decodedMaterializeCommandEnvelope.materialize().project().id() == "corytm-project-schema-proof";

    Command originalMoveClipCommandEnvelope;
    *originalMoveClipCommandEnvelope.mutable_move_clip() = originalMoveCommand;

    std::string serializedMoveClipEnvelope;
    const bool moveClipEnvelopeSerializedOk = originalMoveClipCommandEnvelope.SerializeToString (&serializedMoveClipEnvelope);

    Command decodedMoveClipCommandEnvelope;
    const bool moveClipEnvelopeParsedOk = decodedMoveClipCommandEnvelope.ParseFromString (serializedMoveClipEnvelope);

    const bool moveClipEnvelopeRoundTripOk = moveClipEnvelopeSerializedOk && moveClipEnvelopeParsedOk
                                             && decodedMoveClipCommandEnvelope.has_move_clip()
                                             && ! decodedMoveClipCommandEnvelope.has_materialize()
                                             && decodedMoveClipCommandEnvelope.move_clip().clip_id() == "clip-1";

    Event originalProjectRenderedEventEnvelope;
    *originalProjectRenderedEventEnvelope.mutable_project_rendered() = originalEvent;

    std::string serializedProjectRenderedEnvelope;
    const bool projectRenderedEnvelopeSerializedOk = originalProjectRenderedEventEnvelope.SerializeToString (&serializedProjectRenderedEnvelope);

    Event decodedProjectRenderedEventEnvelope;
    const bool projectRenderedEnvelopeParsedOk = decodedProjectRenderedEventEnvelope.ParseFromString (serializedProjectRenderedEnvelope);

    const bool projectRenderedEnvelopeRoundTripOk = projectRenderedEnvelopeSerializedOk && projectRenderedEnvelopeParsedOk
                                                    && decodedProjectRenderedEventEnvelope.has_project_rendered()
                                                    && ! decodedProjectRenderedEventEnvelope.has_clip_moved()
                                                    && decodedProjectRenderedEventEnvelope.project_rendered().rendered_sample_count() == 110250;

    Event originalClipMovedEventEnvelope;
    *originalClipMovedEventEnvelope.mutable_clip_moved() = originalMovedEvent;

    std::string serializedClipMovedEnvelope;
    const bool clipMovedEnvelopeSerializedOk = originalClipMovedEventEnvelope.SerializeToString (&serializedClipMovedEnvelope);

    Event decodedClipMovedEventEnvelope;
    const bool clipMovedEnvelopeParsedOk = decodedClipMovedEventEnvelope.ParseFromString (serializedClipMovedEnvelope);

    const bool clipMovedEnvelopeRoundTripOk = clipMovedEnvelopeSerializedOk && clipMovedEnvelopeParsedOk
                                              && decodedClipMovedEventEnvelope.has_clip_moved()
                                              && ! decodedClipMovedEventEnvelope.has_project_rendered()
                                              && decodedClipMovedEventEnvelope.clip_moved().moved();

    return commandRoundTripOk && eventRoundTripOk && moveCommandRoundTripOk && movedEventRoundTripOk
                   && materializeEnvelopeRoundTripOk && moveClipEnvelopeRoundTripOk
                   && projectRenderedEnvelopeRoundTripOk && clipMovedEnvelopeRoundTripOk
               ? 0
               : 1;
}
