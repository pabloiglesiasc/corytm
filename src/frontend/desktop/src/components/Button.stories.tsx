import '../main.css'
import Button from './Button'

export const Secondary = () => <Button>Secondary</Button>
export const Primary = () => <Button variant="primary">Primary</Button>
export const Disabled = () => (
  <div className="flex gap-2">
    <Button disabled>Secondary</Button>
    <Button variant="primary" disabled>
      Primary
    </Button>
  </div>
)
