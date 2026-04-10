import './Sidebar.css'

const STATUS_FILTERS = [
  { key: 'all',               label: 'All Tasks',         icon: 'bi-list-task' },
  { key: 'not_started',       label: 'Not Started',       icon: 'bi-hourglass' },
  { key: 'in_progress',       label: 'In Progress',       icon: 'bi-play-circle' },
  { key: 'breached_deadline', label: 'Breached Deadline', icon: 'bi-exclamation-circle' },
  { key: 'done_intime',       label: 'Done',              icon: 'bi-check-circle' },
]

function countByStatus(tasks, key) {
  if (key === 'all') return tasks.length
  return tasks.filter(t => t.status === key).length
}

export default function Sidebar({ tasks, filter, setFilter }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <i className="bi bi-terminal-fill sidebar-logo-icon" />
        <span className="sidebar-title">taskctl</span>
      </div>

      <div className="sidebar-divider" />

      <nav className="sidebar-nav">
        <p className="sidebar-section-label">Filter by status</p>
        {STATUS_FILTERS.map(({ key, label, icon }) => {
          const count = countByStatus(tasks, key)
          return (
            <button
              key={key}
              className={`sidebar-item ${filter === key ? 'active' : ''}`}
              onClick={() => setFilter(key)}
            >
              <i className={`bi ${icon} sidebar-item-icon`} />
              <span className="sidebar-item-label">{label}</span>
              <span className="sidebar-item-badge">{count}</span>
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
