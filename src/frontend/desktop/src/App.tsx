import { useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { open, save } from '@tauri-apps/plugin-dialog'

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

type CommandResult =
  | MoveClipResult
  | ProjectCreatedResult
  | ProjectSavedResult
  | ProjectOpenedResult

const PROJECT_FILE_FILTER = [{ name: 'Corytm Project', extensions: ['json'] }]

function App() {
  const [result, setResult] = useState<CommandResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  // Move Clip targets the hardcoded desktop-fixture track/clip ids.
  // New Project and Open both replace the session's current project
  // with one that may not carry those ids, and the Desktop channel
  // has no defined behavior for a command naming an id that doesn't
  // exist in the current project — so this control is only offered
  // while the session's original fixture project is still current.
  const [fixtureClipAvailable, setFixtureClipAvailable] = useState(true)

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
      return opened
    })
  }

  async function handleMoveClip() {
    await run(() => invoke<MoveClipResult>('move_clip'))
  }

  return (
    <>
      <p>Frontend toolchain proof</p>
      <button onClick={handleCreateProject} disabled={pending}>
        New Project
      </button>
      <button onClick={handleSaveProject} disabled={pending}>
        Save
      </button>
      <button onClick={handleOpenProject} disabled={pending}>
        Open
      </button>
      <button onClick={handleMoveClip} disabled={pending || !fixtureClipAvailable}>
        Move Clip
      </button>
      {result !== null && <pre>{JSON.stringify(result, null, 2)}</pre>}
      {error !== null && <p>{error}</p>}
    </>
  )
}

export default App
