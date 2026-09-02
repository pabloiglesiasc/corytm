import { useState } from 'react'
import { invoke } from '@tauri-apps/api/core'

type MoveClipResult = {
  moved: boolean
  start_seconds: number
  rendered_file_path: string
  rendered_sample_count: number
  peak_amplitude: number
}

function App() {
  const [result, setResult] = useState<MoveClipResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function handleMoveClip() {
    setPending(true)
    setError(null)
    try {
      setResult(await invoke<MoveClipResult>('move_clip'))
    } catch (invokeError) {
      setError(String(invokeError))
    } finally {
      setPending(false)
    }
  }

  return (
    <>
      <p>Frontend toolchain proof</p>
      <button onClick={handleMoveClip} disabled={pending || result !== null}>
        Move Clip
      </button>
      {result !== null && <pre>{JSON.stringify(result, null, 2)}</pre>}
      {error !== null && <p>{error}</p>}
    </>
  )
}

export default App
