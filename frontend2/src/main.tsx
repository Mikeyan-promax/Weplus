import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// 在开发环境中导入测试工具
if (import.meta.env.DEV) {
  import('./utils/testUserDataIsolation');
  import('./utils/functionalityTest');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
