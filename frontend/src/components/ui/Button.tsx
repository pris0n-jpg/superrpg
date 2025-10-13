import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

// 按钮变体配置
const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 shadow-sm',
        secondary: 'bg-secondary-200 dark:bg-secondary-700 text-secondary-900 dark:text-secondary-100 hover:bg-secondary-300 dark:hover:bg-secondary-600 focus:ring-secondary-500',
        outline: 'border border-secondary-300 dark:border-secondary-600 bg-transparent text-secondary-700 dark:text-secondary-300 hover:bg-secondary-50 dark:hover:bg-secondary-800 focus:ring-secondary-500',
        ghost: 'bg-transparent text-secondary-700 dark:text-secondary-300 hover:bg-secondary-100 dark:hover:bg-secondary-800 focus:ring-secondary-500',
        danger: 'bg-error-600 text-white hover:bg-error-700 focus:ring-error-500 shadow-sm',
        warning: 'bg-warning-600 text-white hover:bg-warning-700 focus:ring-warning-500 shadow-sm',
        success: 'bg-success-600 text-white hover:bg-success-700 focus:ring-success-500 shadow-sm',
      },
      size: {
        xs: 'px-2.5 py-1.5 text-xs',
        sm: 'px-3 py-2 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
        xl: 'px-8 py-4 text-xl',
      },
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      fullWidth: false,
    },
  }
)

// 按钮图标变体
const iconVariants = cva('', {
  variants: {
    size: {
      xs: 'h-3 w-3',
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
      xl: 'h-7 w-7',
    },
    position: {
      left: '-ml-1 mr-2',
      right: '-mr-1 ml-2',
      only: 'mr-0',
    },
  },
  defaultVariants: {
    size: 'md',
    position: 'left',
  },
})

// 按钮加载动画
const LoadingSpinner = ({ size }: { size: string }) => (
  <svg
    className={cn('animate-spin', {
      'h-3 w-3': size === 'xs',
      'h-4 w-4': size === 'sm',
      'h-5 w-5': size === 'md',
      'h-6 w-6': size === 'lg',
      'h-7 w-7': size === 'xl',
    })}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

// 按钮组件接口
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right' | 'only'
  children?: React.ReactNode
}

// 按钮组件
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      loading = false,
      icon,
      iconPosition = 'left',
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading

    return (
      <button
        className={cn(buttonVariants({ variant, size, fullWidth }), className)}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {loading && <LoadingSpinner size={size || 'md'} />}
        {!loading && icon && (
          <span className={cn(iconVariants({ size, position: iconPosition }))}>
            {icon}
          </span>
        )}
        {children && iconPosition !== 'only' && (
          <span className={cn({ 'ml-2': icon && iconPosition === 'left' })}>
            {children}
          </span>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button