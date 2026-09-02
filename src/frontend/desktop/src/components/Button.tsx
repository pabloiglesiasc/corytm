import type { ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

const BASE_CLASSES =
  'rounded-sm border px-4 py-2 font-sans text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60'

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: 'border-accent bg-accent text-accent-contrast hover:bg-accent-hover',
  secondary: 'border-border bg-surface text-text hover:bg-surface-hover',
}

function Button({ variant = 'secondary', className, ...rest }: ButtonProps) {
  const classes = [BASE_CLASSES, VARIANT_CLASSES[variant], className]
    .filter(Boolean)
    .join(' ')

  return <button className={classes} {...rest} />
}

export default Button
