import { useState, useEffect, useCallback } from 'react'
import Sidebar from '../components/Sidebar'
import TaskList from '../components/TaskList'
import TaskDetail from '../components/TaskDetail'
import { authorizedFetch } from '../lib/auth.js'
import './App.css'

export default function App({ onLogout, username }) {
  const [tasks, setTasks] = useState([])
  const [filter, setFilter] = useState('all')
  const [days, setDays] = useState(7)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTask, setSelectedTask] = useState(null)

  const fetchTasks = useCallback(() => {
    setLoading(true)
    setError(null)
    authorizedFetch(`/api/tasks?days=${days}`)
      .then(r => {
        if (!r.ok) throw new Error(`Server error: ${r.status}`)
        return r.json()
      })
      .then(data => {
        setTasks(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [days])

  useEffect(() => { fetchTasks() }, [fetchTasks])

  const filtered = filter === 'all'
    ? tasks
    : tasks.filter(t => t.status === filter)

  return (
    <div className="app-layout">
      <Sidebar tasks={tasks} filter={filter} setFilter={setFilter} onLogoClick={() => setSelectedTask(null)} username={username} onLogout={onLogout} />
      {selectedTask
        ? <TaskDetail task={selectedTask} onClose={() => setSelectedTask(null)} />
        : <TaskList
            tasks={filtered}
            loading={loading}
            error={error}
            days={days}
            setDays={setDays}
            onRefresh={fetchTasks}
            onTaskClick={setSelectedTask}
          />
      }
    </div>
  )
}
