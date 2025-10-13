import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

// 模态框变体配置
const modalVariants = cva(
  'fixed inset-0 z-50 flex items-center justify-center p-4',
  {
    variants: {
      size: {
        xs: 'max-w-xs',
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
        '2xl': 'max-w-2xl',
        '3xl': 'max-w-3xl',
        '4xl': 'max-w-4xl',
        '5xl': 'max-w-5xl',
        full: 'max-w-full mx-4',
      },
      position: {
        center: 'items-center justify-center',
        top: 'items-start justify-center pt-16',
        bottom: 'items-end justify-center pb-16',
      },
    },
    defaultVariants: {
      size: 'md',
      position: 'center',
    },
  }
)

// 模态框内容变体配置
const modalContentVariants = cva(
  'relative bg-white dark:bg-secondary-800 rounded-xl shadow-strong border border-secondary-200 dark:border-secondary-700 max-h-full overflow-hidden',
  {
    variants: {
      size: {
        xs: 'w-full max-h-[90vh]',
        sm: 'w-full max-h-[90vh]',
        md: 'w-full max-h-[90vh]',
        lg: 'w-full max-h-[90vh]',
        xl: 'w-full max-h-[90vh]',
        '2xl': 'w-full max-h-[90vh]',
        '3xl': 'w-full max-h-[90vh]',
        '4xl': 'w-full max-h-[90vh]',
        '5xl': 'w-full max-h-[90vh]',
        full: 'w-full h-[90vh]',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

// 模态框头部变体配置
const modalHeaderVariants = cva(
  'flex items-center justify-between p-6 border-b border-secondary-200 dark:border-secondary-700',
  {
    variants: {
      size: {
        xs: 'p-4',
        sm: 'p-5',
        md: 'p-6',
        lg: 'p-6',
        xl: 'p-6',
        '2xl': 'p-6',
        '3xl': 'p-6',
        '4xl': 'p-6',
        '5xl': 'p-6',
        full: 'p-6',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

// 模态框内容变体配置
const modalBodyVariants = cva(
  'p-6 overflow-y-auto',
  {
    variants: {
      size: {
        xs: 'p-4',
        sm: 'p-5',
        md: 'p-6',
        lg: 'p-6',
        xl: 'p-6',
        '2xl': 'p-6',
        '3xl': 'p-6',
        '4xl': 'p-6',
        '5xl': 'p-6',
        full: 'p-6',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

// 模态框底部变体配置
const modalFooterVariants = cva(
  'flex items-center justify-between p-6 border-t border-secondary-200 dark:border-secondary-700 bg-secondary-50 dark:bg-secondary-900/50',
  {
    variants: {
      size: {
        xs: 'p-4',
        sm: 'p-5',
        md: 'p-6',
        lg: 'p-6',
        xl: 'p-6',
        '2xl': 'p-6',
        '3xl': 'p-6',
        '4xl': 'p-6',
        '5xl': 'p-6',
        full: 'p-6',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

// 模态框组件接口
export interface ModalProps extends VariantProps<typeof modalVariants> {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
  preventBodyScroll?: boolean
  className?: string
  overlayClassName?: string
}

// 模态框头部组件接口
export interface ModalHeaderProps {
  title?: string
  description?: string
  onClose?: () => void
  showCloseButton?: boolean
  className?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full'
}

// 模态框内容组件接口
export interface ModalBodyProps {
  children: React.ReactNode
  className?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full'
}

// 模态框底部组件接口
export interface ModalFooterProps {
  children: React.ReactNode
  className?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full'
}

// 关闭按钮组件
const CloseButton = ({ onClose, className }: { onClose: () => void; className?: string }) => (
  <button
    type="button"
    className={cn(
      'rounded-lg p-2 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 dark:hover:bg-secondary-700 focus:outline-none focus:ring-2 focus:ring-primary-500',
      className
    )}
    onClick={onClose}
  >
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  </button>
)

// 模态框组件
const Modal = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size,
  position,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  preventBodyScroll = true,
  className,
  overlayClassName,
}: ModalProps) => {
  const modalRef = useRef<HTMLDivElement>(null)

  // 处理ESC键关闭
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, closeOnEscape, onClose])

  // 防止背景滚动
  useEffect(() => {
    if (!isOpen || !preventBodyScroll) return

    const originalStyle = window.getComputedStyle(document.body).overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.body.style.overflow = originalStyle
    }
  }, [isOpen, preventBodyScroll])

  // 处理焦点管理
  useEffect(() => {
    if (!isOpen) return

    const focusableElements = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>

    if (focusableElements.length > 0) {
      focusableElements[0].focus()
    }
  }, [isOpen])

  // 处理覆盖层点击
  const handleOverlayClick = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget && closeOnOverlayClick) {
      onClose()
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div className="fixed inset-0 z-50">
      {/* 覆盖层 */}
      <div
        className={cn(
          'absolute inset-0 bg-black/50 backdrop-blur-sm',
          overlayClassName
        )}
        onClick={handleOverlayClick}
      />
      
      {/* 模态框 */}
      <div className={cn(modalVariants({ size, position }), className)}>
        <div
          ref={modalRef}
          className={cn(modalContentVariants({ size }))}
          role="dialog"
          aria-modal="true"
          aria-labelledby={title ? 'modal-title' : undefined}
          aria-describedby={description ? 'modal-description' : undefined}
        >
          {children}
        </div>
      </div>
    </div>,
    document.body
  )
}

// 模态框头部组件
const ModalHeader = ({
  title,
  description,
  onClose,
  showCloseButton = true,
  className,
  size = 'md',
}: ModalHeaderProps) => (
  <div className={cn(modalHeaderVariants({ size }), className)}>
    <div className="flex-1">
      {title && (
        <h2 id="modal-title" className="text-lg font-semibold text-secondary-900 dark:text-secondary-100">
          {title}
        </h2>
      )}
      {description && (
        <p id="modal-description" className="text-sm text-secondary-600 dark:text-secondary-400 mt-1">
          {description}
        </p>
      )}
    </div>
    {showCloseButton && onClose && <CloseButton onClose={onClose} />}
  </div>
)

// 模态框内容组件
const ModalBody = ({ children, className, size = 'md' }: ModalBodyProps) => (
  <div className={cn(modalBodyVariants({ size }), className)}>
    {children}
  </div>
)

// 模态框底部组件
const ModalFooter = ({ children, className, size = 'md' }: ModalFooterProps) => (
  <div className={cn(modalFooterVariants({ size }), className)}>
    {children}
  </div>
)

export { Modal, ModalHeader, ModalBody, ModalFooter }

export default Modal