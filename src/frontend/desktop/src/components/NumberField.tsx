import type { InputHTMLAttributes } from 'react'

type NumberFieldProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'type' | 'onChange' | 'value'
> & {
  label: string
  value: number
  onValueChange: (value: number) => void
}

function NumberField({
  label,
  value,
  onValueChange,
  id,
  className,
  ...rest
}: NumberFieldProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')

  return (
    <label className="flex flex-col gap-1" htmlFor={inputId}>
      <span className="text-text-muted font-sans text-xs">{label}</span>
      <input
        id={inputId}
        type="number"
        className={[
          'w-32 rounded-sm border border-border bg-surface px-3 py-2 font-sans text-sm text-text disabled:cursor-not-allowed disabled:opacity-60',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
        value={value}
        onChange={(event) => onValueChange(event.target.valueAsNumber)}
        {...rest}
      />
    </label>
  )
}

export default NumberField
