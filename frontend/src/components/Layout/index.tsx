import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'

const Layout = () => {
  return (
    <div className="min-h-screen bg-secondary-50 dark:bg-secondary-900">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 md:ml-64 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout