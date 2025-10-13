import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// 合并Tailwind CSS类名的工具函数
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 条件类名工具函数
export function conditionalClass(condition: boolean, className: string) {
  return condition ? className : ''
}

// 响应式类名工具函数
export function responsiveClass(
  base: string,
  sm?: string,
  md?: string,
  lg?: string,
  xl?: string
) {
  const classes = [base]
  if (sm) classes.push(`sm:${sm}`)
  if (md) classes.push(`md:${md}`)
  if (lg) classes.push(`lg:${lg}`)
  if (xl) classes.push(`xl:${xl}`)
  return classes.join(' ')
}

// 主题相关类名工具函数
export function themeClass(lightClass: string, darkClass?: string) {
  return darkClass ? `${lightClass} dark:${darkClass}` : lightClass
}

// 状态类名工具函数
export function stateClass(
  base: string,
  active?: string,
  disabled?: string,
  loading?: string
) {
  const classes = [base]
  if (active) classes.push(active)
  if (disabled) classes.push(disabled)
  if (loading) classes.push(loading)
  return classes.join(' ')
}

// 动画类名工具函数
export function animationClass(animation: string) {
  const animations: Record<string, string> = {
    fade: 'animate-fade-in',
    slide: 'animate-slide-in',
    bounce: 'animate-bounce-in',
    pulse: 'animate-pulse-slow',
    spin: 'animate-spin',
  }
  return animations[animation] || ''
}

// 尺寸类名工具函数
export function sizeClass(size: 'xs' | 'sm' | 'md' | 'lg' | 'xl', prefix: string) {
  const sizes: Record<string, string> = {
    xs: `${prefix}-xs`,
    sm: `${prefix}-sm`,
    md: `${prefix}-md`,
    lg: `${prefix}-lg`,
    xl: `${prefix}-xl`,
  }
  return sizes[size] || sizes.md
}

// 颜色类名工具函数
export function colorClass(
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info',
  shade: 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 950,
  type: 'bg' | 'text' | 'border' | 'ring' | 'shadow' = 'bg'
) {
  return `${type}-${color}-${shade}`
}

// 间距类名工具函数
export function spacingClass(
  spacing: number | string,
  direction: 'all' | 'x' | 'y' | 'top' | 'bottom' | 'left' | 'right' = 'all',
  type: 'm' | 'p' = 'm'
) {
  const prefix = `${type}`
  const suffix = direction === 'all' ? '' : `-${direction}`
  return `${prefix}${suffix}-${spacing}`
}

// 圆角类名工具函数
export function roundedClass(
  size: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full' = 'md'
) {
  const sizes: Record<string, string> = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    '3xl': 'rounded-3xl',
    full: 'rounded-full',
  }
  return sizes[size]
}

// 阴影类名工具函数
export function shadowClass(
  size: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'inner' = 'md'
) {
  const shadows: Record<string, string> = {
    none: 'shadow-none',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
    '2xl': 'shadow-2xl',
    inner: 'shadow-inner',
  }
  return shadows[size]
}

// 字体大小类名工具函数
export function fontSizeClass(
  size: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl' = 'base'
) {
  const sizes: Record<string, string> = {
    xs: 'text-xs',
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
    '2xl': 'text-2xl',
    '3xl': 'text-3xl',
    '4xl': 'text-4xl',
    '5xl': 'text-5xl',
    '6xl': 'text-6xl',
  }
  return sizes[size]
}

// 字体粗细类名工具函数
export function fontWeightClass(
  weight: 'thin' | 'light' | 'normal' | 'medium' | 'semibold' | 'bold' | 'extrabold' | 'black' = 'normal'
) {
  const weights: Record<string, string> = {
    thin: 'font-thin',
    light: 'font-light',
    normal: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold',
    extrabold: 'font-extrabold',
    black: 'font-black',
  }
  return weights[weight]
}

// 文本对齐类名工具函数
export function textAlignClass(
  align: 'left' | 'center' | 'right' | 'justify' = 'left'
) {
  const aligns: Record<string, string> = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
    justify: 'text-justify',
  }
  return aligns[align]
}

// 显示类名工具函数
export function displayClass(
  display: 'block' | 'inline' | 'inline-block' | 'flex' | 'inline-flex' | 'grid' | 'hidden' = 'block'
) {
  const displays: Record<string, string> = {
    block: 'block',
    inline: 'inline',
    'inline-block': 'inline-block',
    flex: 'flex',
    'inline-flex': 'inline-flex',
    grid: 'grid',
    hidden: 'hidden',
  }
  return displays[display]
}

// 位置类名工具函数
export function positionClass(
  position: 'static' | 'fixed' | 'absolute' | 'relative' | 'sticky' = 'static'
) {
  const positions: Record<string, string> = {
    static: 'static',
    fixed: 'fixed',
    absolute: 'absolute',
    relative: 'relative',
    sticky: 'sticky',
  }
  return positions[position]
}

// 溢出类名工具函数
export function overflowClass(
  overflow: 'auto' | 'hidden' | 'visible' | 'scroll' | 'clip' = 'visible',
  direction: 'x' | 'y' | '' = ''
) {
  const suffix = direction ? `-${direction}` : ''
  return `overflow${suffix}-${overflow}`
}

// 光标类名工具函数
export function cursorClass(
  cursor: 'auto' | 'default' | 'pointer' | 'wait' | 'text' | 'move' | 'help' | 'not-allowed' = 'auto'
) {
  const cursors: Record<string, string> = {
    auto: 'cursor-auto',
    default: 'cursor-default',
    pointer: 'cursor-pointer',
    wait: 'cursor-wait',
    text: 'cursor-text',
    move: 'cursor-move',
    help: 'cursor-help',
    'not-allowed': 'cursor-not-allowed',
  }
  return cursors[cursor]
}

// 用户选择类名工具函数
export function selectClass(
  select: 'none' | 'text' | 'all' | 'auto' = 'auto'
) {
  const selects: Record<string, string> = {
    none: 'select-none',
    text: 'select-text',
    all: 'select-all',
    auto: 'select-auto',
  }
  return selects[select]
}

// 指针事件类名工具函数
export function pointerEventsClass(
  events: 'none' | 'auto' = 'auto'
) {
  const eventsMap: Record<string, string> = {
    none: 'pointer-events-none',
    auto: 'pointer-events-auto',
  }
  return eventsMap[events]
}