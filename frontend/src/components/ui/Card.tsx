import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

// 卡片变体配置
const cardVariants = cva(
  'rounded-xl border transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'bg-white dark:bg-secondary-800 border-secondary-200 dark:border-secondary-700 shadow-soft',
        elevated: 'bg-white dark:bg-secondary-800 border-secondary-200 dark:border-secondary-700 shadow-medium',
        outlined: 'bg-white dark:bg-secondary-800 border-secondary-300 dark:border-secondary-600 shadow-none',
        filled: 'bg-secondary-50 dark:bg-secondary-900 border-secondary-200 dark:border-secondary-700 shadow-none',
        ghost: 'bg-transparent border-secondary-200 dark:border-secondary-700 shadow-none hover:bg-secondary-50 dark:hover:bg-secondary-800',
      },
      size: {
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
        xl: 'p-10',
      },
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
      interactive: {
        true: 'cursor-pointer hover:shadow-medium hover:border-primary-300 dark:hover:border-primary-600',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      fullWidth: true,
      interactive: false,
    },
  }
)

// 卡片头部变体配置
const cardHeaderVariants = cva(
  'flex items-center justify-between',
  {
    variants: {
      size: {
        sm: 'mb-3',
        md: 'mb-4',
        lg: 'mb-6',
        xl: 'mb-8',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

// 卡片内容变体配置
const cardContentVariants = cva('', {
  variants: {
    size: {
      sm: '',
      md: '',
      lg: '',
      xl: '',
    },
  },
  defaultVariants: {
    size: 'md',
  },
})

// 卡片底部变体配置
const cardFooterVariants = cva(
  'flex items-center justify-between mt-4 pt-4 border-t border-secondary-200 dark:border-secondary-700',
  {
    variants: {
      size: {
        sm: 'mt-3 pt-3',
        md: 'mt-4 pt-4',
        lg: 'mt-6 pt-6',
        xl: 'mt-8 pt-8',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

// 卡片组件接口
export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  children: React.ReactNode
}

// 卡片头部组件接口
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  action?: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

// 卡片内容组件接口
export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

// 卡片底部组件接口
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

// 卡片组件
const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, size, fullWidth, interactive, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, size, fullWidth, interactive }), className)}
      {...props}
    >
      {children}
    </div>
  )
)

Card.displayName = 'Card'

// 卡片头部组件
const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, description, action, size, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardHeaderVariants({ size }), className)}
      {...props}
    >
      <div className="flex-1">
        {title && (
          <h3 className="text-lg font-semibold text-secondary-900 dark:text-secondary-100">
            {title}
          </h3>
        )}
        {description && (
          <p className="text-sm text-secondary-600 dark:text-secondary-400 mt-1">
            {description}
          </p>
        )}
        {children}
      </div>
      {action && <div className="flex-shrink-0 ml-4">{action}</div>}
    </div>
  )
)

CardHeader.displayName = 'CardHeader'

// 卡片内容组件
const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, size, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardContentVariants({ size }), className)}
      {...props}
    >
      {children}
    </div>
  )
)

CardContent.displayName = 'CardContent'

// 卡片底部组件
const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, size, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardFooterVariants({ size }), className)}
      {...props}
    >
      {children}
    </div>
  )
)

CardFooter.displayName = 'CardFooter'

// 卡片标题组件
const CardTitle = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, children, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-lg font-semibold text-secondary-900 dark:text-secondary-100', className)}
      {...props}
    >
      {children}
    </h3>
  )
)

CardTitle.displayName = 'CardTitle'

// 卡片描述组件
const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-secondary-600 dark:text-secondary-400', className)}
      {...props}
    >
      {children}
    </p>
  )
)

CardDescription.displayName = 'CardDescription'

export {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  CardTitle,
  CardDescription,
}

export default Card