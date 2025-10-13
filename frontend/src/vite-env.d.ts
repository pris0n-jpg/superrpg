/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE?: string
  readonly VITE_APP_VERSION?: string
  readonly VITE_API_BASE_URL?: string
  readonly VITE_API_URL?: string
  readonly VITE_API_TIMEOUT?: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  interface Window {
    __APP_LOADING__?: boolean
  }
}
