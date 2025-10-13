import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

// 输入框变体配置
const inputVariants = cva(
  'w-full px-3 py-2 border rounded-lg bg-white dark:bg-secondary-800 text-secondary-900 dark:text-secondary-100 placeholder-secondary-500 dark:placeholder-secondary-400 focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        default: 'border-secondary-300 dark:border-secondary-600 focus:border-primary-500 focus:ring-primary-500',
        error: 'border-error-500 focus:border-error-500 focus:ring-error-500',
        success: 'border-success-500 focus:border-success-500 focus:ring-success-500',
        warning: 'border-warning-500 focus:border-warning-500 focus:ring-warning-500',
      },
      size: {
        xs: 'px-2 py-1 text-xs',
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-3 py-2 text-base',
        lg: 'px-4 py-3 text-lg',
        xl: 'px-5 py-4 text-xl',
      },
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      fullWidth: true,
    },
  }
)

// 输入框组件接口
export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  label?: string
  description?: string
  error?: string
  success?: string
  warning?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  containerClassName?: string
}

// 输入框组件
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      label,
      description,
      error,
      success,
      warning,
      leftIcon,
      rightIcon,
      containerClassName,
      id,
      ...props
    },
    ref
  ) => {
    // 确定变体优先级
    const inputVariant = error ? 'error' : success ? 'success' : warning ? 'warning' : variant
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`

    return (
      <div className={cn('space-y-2', containerClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-secondary-700 dark:text-secondary-300"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <div className={cn(
                'text-secondary-400',
                {
                  'h-3 w-3': size === 'xs',
                  'h-4 w-4': size === 'sm',
                  'h-5 w-5': size === 'md',
                  'h-6 w-6': size === 'lg',
                  'h-7 w-7': size === 'xl',
                }
              )}>
                {leftIcon}
              </div>
            </div>
          )}
          
          <input
            id={inputId}
            className={cn(
              inputVariants({ variant: inputVariant, size, fullWidth }),
              {
                'pl-10': leftIcon && (size === 'md' || size === 'lg'),
                'pl-9': leftIcon && size === 'sm',
                'pl-8': leftIcon && size === 'xs',
                'pl-11': leftIcon && size === 'xl',
                'pr-10': rightIcon && (size === 'md' || size === 'lg'),
                'pr-9': rightIcon && size === 'sm',
                'pr-8': rightIcon && size === 'xs',
                'pr-11': rightIcon && size === 'xl',
              },
              className
            )}
            ref={ref}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <div className={cn(
                'text-secondary-400',
                {
                  'h-3 w-3': size === 'xs',
                  'h-4 w-4': size === 'sm',
                  'h-5 w-5': size === 'md',
                  'h-6 w-6': size === 'lg',
                  'h-7 w-7': size === 'xl',
                }
              )}>
                {rightIcon}
              </div>
            </div>
          )}
        </div>
        
        {description && (
          <p className="text-xs text-secondary-500 dark:text-secondary-400">
            {description}
          </p>
        )}
        
        {error && (
          <p className="text-xs text-error-600 dark:text-error-400">
            {error}
          </p>
        )}
        
        {success && (
          <p className="text-xs text-success-600 dark:text-success-400">
            {success}
          </p>
        )}
        
        {warning && (
          <p className="text-xs text-warning-600 dark:text-warning-400">
            {warning}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input