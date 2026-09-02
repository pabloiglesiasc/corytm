import { useState } from 'react'
import '../main.css'
import NumberField from './NumberField'

export const Default = () => {
  const [value, setValue] = useState(2)
  return (
    <NumberField
      label="Clip duration (seconds)"
      value={value}
      onValueChange={setValue}
      min={0.1}
      step={0.1}
    />
  )
}

export const Disabled = () => (
  <NumberField
    label="Clip duration (seconds)"
    value={2}
    onValueChange={() => {}}
    disabled
  />
)
