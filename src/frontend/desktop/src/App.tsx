import { useEffect, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { open, save } from '@tauri-apps/plugin-dialog'
import Button from './components/Button'
import NumberField from './components/NumberField'

type MoveClipResult = {
  moved: boolean
  start_seconds: number
  rendered_file_path: string
  rendered_sample_count: number
  peak_amplitude: number
}

type ProjectCreatedResult = {
  project_id: string
}

type ProjectSavedResult = {
  project_id: string
  file_path: string
}

type ProjectOpenedResult = {
  project_id: string
  file_path: string
  track_count: number
  rendered_sample_count: number
  peak_amplitude: number
}

type AudioTrackAddedResult = {
  track_id: string
  track_count: number
}

type AudioClipAddedResult = {
  clip_id: string
  start_seconds: number
  duration_seconds: number
  rendered_file_path: string
  rendered_sample_count: number
  peak_amplitude: number
}

type PlaybackStartedResult = {
  device_opened: boolean
}

type PlaybackPositionResult = {
  is_playing: boolean
  position_seconds: number
}

type PlaybackStoppedResult = {
  final_position_seconds: number
}

type CommandResult =
  | MoveClipResult
  | ProjectCreatedResult
  | ProjectSavedResult
  | ProjectOpenedResult
  | AudioTrackAddedResult
  | AudioClipAddedResult
  | PlaybackStartedResult
  | PlaybackStoppedResult

const PROJECT_FILE_FILTER = [{ name: 'Corytm Project', extensions: ['json'] }]
const DEFAULT_CLIP_DURATION_SECONDS = 2
const CHANNEL_READY_POLL_INTERVAL_MS = 200
const CHANNEL_READY_STEADY_POLL_INTERVAL_MS = 2000
const PLAYBACK_POSITION_POLL_INTERVAL_MS = 200

function formatPlaybackPosition(totalSeconds: number): string {
  const wholeSeconds = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(wholeSeconds / 60)
  const seconds = wholeSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function App() {
  const [result, setResult] = useState<CommandResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  // The Desktop channel connects asynchronously after the window
  // already appears (spawning the sidecar and authenticating takes
  // real time), and — since this channel is genuinely persistent for
  // the app's whole session, never silently reconnected — it can also
  // later die (the peer process exiting) while the app stays open. A
  // user must never be able to click a control while either is true,
  // so every control below stays disabled until this is confirmed
  // `true` by the backend itself, continuously, not assumed from the
  // window merely being visible or from having been true once before.
  const [channelReady, setChannelReady] = useState(false)
  const [hasEverBeenReady, setHasEverBeenReady] = useState(false)
  // Move Clip targets the hardcoded desktop-fixture track/clip ids.
  // New Project and Open both replace the session's current project
  // with one that may not carry those ids, and the Desktop channel
  // has no defined behavior for a command naming an id that doesn't
  // exist in the current project — so this control is only offered
  // while the session's original fixture project is still current.
  const [fixtureClipAvailable, setFixtureClipAvailable] = useState(true)
  // The session starts with the fixture project, which already has
  // one track — and the Native Audio Runtime only ever materializes
  // a project's first track, so a second one would silently never
  // render. Add Track is only offered once the current project is
  // known to have none yet.
  const [canAddTrack, setCanAddTrack] = useState(false)
  // Add Clip needs a concrete track id to target, which this session
  // only ever learns from its own Add Track response — re-opening a
  // project that already has a track doesn't tell the frontend that
  // track's id, so Add Clip stays unavailable in that case, mirroring
  // Move Clip's own fixture-only limitation above.
  const [trackId, setTrackId] = useState<string | null>(null)
  const [clipDuration, setClipDuration] = useState(DEFAULT_CLIP_DURATION_SECONDS)
  // Play needs at least one clip to materialize a playable Edit from —
  // set once Add Clip succeeds, or once Open reports genuine rendered
  // output (a reliable proxy for "this project has audio to play",
  // since track_count alone doesn't distinguish an empty track from
  // one with clips).
  const [hasClip, setHasClip] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [playbackPositionSeconds, setPlaybackPositionSeconds] = useState(0)

  useEffect(() => {
    let cancelled = false
    let currentlyReady = false

    async function poll() {
      if (cancelled) {
        return
      }
      const ready = await invoke<boolean>('desktop_channel_ready')
      if (cancelled) {
        return
      }
      if (ready !== currentlyReady) {
        currentlyReady = ready
        setChannelReady(ready)
        if (ready) {
          setHasEverBeenReady(true)
        }
      }
      setTimeout(
        poll,
        currentlyReady
          ? CHANNEL_READY_STEADY_POLL_INTERVAL_MS
          : CHANNEL_READY_POLL_INTERVAL_MS,
      )
    }

    poll()

    return () => {
      cancelled = true
    }
  }, [])

  async function run(action: () => Promise<CommandResult | null>) {
    setPending(true)
    setError(null)
    try {
      const value = await action()
      if (value !== null) {
        setResult(value)
      }
    } catch (invokeError) {
      setError(String(invokeError))
    } finally {
      setPending(false)
    }
  }

  async function handleCreateProject() {
    await run(async () => {
      const created = await invoke<ProjectCreatedResult>('create_project')
      setFixtureClipAvailable(false)
      setCanAddTrack(true)
      setTrackId(null)
      setHasClip(false)
      return created
    })
  }

  async function handleSaveProject() {
    await run(async () => {
      const filePath = await save({ filters: PROJECT_FILE_FILTER })
      if (filePath === null) {
        return null
      }
      return invoke<ProjectSavedResult>('save_project', { filePath })
    })
  }

  async function handleOpenProject() {
    await run(async () => {
      const filePath = await open({
        multiple: false,
        directory: false,
        filters: PROJECT_FILE_FILTER,
      })
      if (filePath === null) {
        return null
      }
      const opened = await invoke<ProjectOpenedResult>('open_project', {
        filePath,
      })
      setFixtureClipAvailable(false)
      setCanAddTrack(opened.track_count === 0)
      setTrackId(null)
      setHasClip(opened.rendered_sample_count > 0)
      return opened
    })
  }

  async function handleMoveClip() {
    await run(() => invoke<MoveClipResult>('move_clip'))
  }

  async function handleAddTrack() {
    await run(async () => {
      const added = await invoke<AudioTrackAddedResult>('add_track')
      setCanAddTrack(false)
      setTrackId(added.track_id)
      return added
    })
  }

  async function handleAddClip() {
    if (trackId === null) {
      return
    }
    await run(async () => {
      const added = await invoke<AudioClipAddedResult>('add_clip', {
        trackId,
        durationSeconds: clipDuration,
      })
      setHasClip(true)
      return added
    })
  }

  async function handlePlay() {
    await run(async () => {
      const started = await invoke<PlaybackStartedResult>('play')
      if (started.device_opened) {
        setPlaybackPositionSeconds(0)
        setPlaying(true)
      }
      return started
    })
  }

  async function handleStop() {
    await run(async () => {
      const stopped = await invoke<PlaybackStoppedResult>('stop')
      setPlaying(false)
      return stopped
    })
  }

  useEffect(() => {
    if (!playing) {
      return
    }
    let cancelled = false

    async function poll() {
      if (cancelled) {
        return
      }
      try {
        const position = await invoke<PlaybackPositionResult>(
          'get_playback_position',
        )
        if (cancelled) {
          return
        }
        setPlaybackPositionSeconds(position.position_seconds)
        if (!position.is_playing) {
          setPlaying(false)
          return
        }
      } catch (pollError) {
        if (!cancelled) {
          setPlaying(false)
          setError(String(pollError))
        }
        return
      }
      setTimeout(poll, PLAYBACK_POSITION_POLL_INTERVAL_MS)
    }

    poll()

    return () => {
      cancelled = true
    }
  }, [playing])

  const controlsDisabled = pending || !channelReady || playing

  return (
    <div className="flex min-h-screen flex-col">
      {!channelReady && (
        <div className="border-border bg-surface text-text-muted border-b px-6 py-2 font-sans text-sm">
          {hasEverBeenReady
            ? 'Backend connection lost — restart Corytm to continue.'
            : 'Connecting to backend…'}
        </div>
      )}
      <header className="border-border border-b px-6 py-4">
        <h1 className="text-text font-sans text-lg font-semibold">Corytm</h1>
        <p className="text-text-muted font-sans text-xs">
          Desktop — Alpha proof of manual editing
        </p>
      </header>
      <main className="flex flex-1 flex-wrap items-start gap-6 p-6">
        <section className="border-border bg-surface rounded-md border p-4">
          <h2 className="text-text mb-3 font-sans text-sm font-semibold">
            Project
          </h2>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="primary"
              onClick={handleCreateProject}
              disabled={controlsDisabled}
            >
              New Project
            </Button>
            <Button onClick={handleSaveProject} disabled={controlsDisabled}>
              Save
            </Button>
            <Button onClick={handleOpenProject} disabled={controlsDisabled}>
              Open
            </Button>
          </div>
        </section>
        <section className="border-border bg-surface rounded-md border p-4">
          <h2 className="text-text mb-3 font-sans text-sm font-semibold">
            Track &amp; Clip
          </h2>
          <div className="flex flex-wrap items-end gap-2">
            <Button
              onClick={handleMoveClip}
              disabled={controlsDisabled || !fixtureClipAvailable}
            >
              Move Clip
            </Button>
            <Button
              onClick={handleAddTrack}
              disabled={controlsDisabled || !canAddTrack}
            >
              Add Track
            </Button>
            <NumberField
              label="Clip duration (seconds)"
              value={clipDuration}
              onValueChange={setClipDuration}
              min={0.1}
              step={0.1}
              disabled={controlsDisabled || trackId === null}
            />
            <Button
              onClick={handleAddClip}
              disabled={controlsDisabled || trackId === null}
            >
              Add Clip
            </Button>
          </div>
        </section>
        <section className="border-border bg-surface rounded-md border p-4">
          <h2 className="text-text mb-3 font-sans text-sm font-semibold">
            Playback
          </h2>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="primary"
              onClick={handlePlay}
              disabled={controlsDisabled || !hasClip}
            >
              Play
            </Button>
            <Button
              onClick={handleStop}
              disabled={pending || !channelReady || !playing}
            >
              Stop
            </Button>
            <span role="status" className="text-text-muted font-sans text-xs">
              {playing ? 'Playing' : 'Stopped'}
            </span>
            <span className="text-text-muted flex items-center gap-2 font-mono text-xs">
              {playing && (
                <span
                  aria-hidden="true"
                  className="bg-accent h-2 w-2 rounded-full"
                />
              )}
              {formatPlaybackPosition(playbackPositionSeconds)}
            </span>
          </div>
        </section>
      </main>
      {(result !== null || error !== null) && (
        <section className="border-border border-t px-6 py-4">
          <h2 className="text-text-muted mb-2 font-sans text-xs font-semibold tracking-wide uppercase">
            Output
          </h2>
          {result !== null && (
            <pre className="border-border bg-surface text-text overflow-x-auto rounded-md border p-3 font-mono text-xs">
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
          {error !== null && (
            <p className="border-border bg-surface text-text rounded-md border p-3 text-xs">
              {error}
            </p>
          )}
        </section>
      )}
    </div>
  )
}

export default App
