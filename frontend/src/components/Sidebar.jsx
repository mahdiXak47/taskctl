import './Sidebar.css'

const STATUS_FILTERS = [
  { key: 'all',               label: 'All Tasks',         icon: 'bi-list-task' },
  { key: 'not_started',       label: 'Not Started',       icon: 'bi-hourglass' },
  { key: 'in_progress',       label: 'In Progress',       icon: 'bi-play-circle' },
  { key: 'breached_deadline', label: 'Breached Deadline', icon: 'bi-exclamation-circle' },
  { key: 'done_intime',       label: 'Done',              icon: 'bi-check-circle' },
  { key: 'done_but_breached', label: 'Done (Late)',        icon: 'bi-check-circle' },
]

function countByStatus(tasks, key) {
  if (key === 'all') return tasks.length
  return tasks.filter(t => t.status === key).length
}

export default function Sidebar({ tasks, filter, setFilter, username, onLogout }) {
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

      <div className="sidebar-footer">
        <div className="sidebar-divider" style={{ margin: '0 0.75rem 0.5rem' }} />
        <div className="sidebar-user">
          <i className="bi bi-person-circle sidebar-user-icon" />
          <span className="sidebar-user-name">{username}</span>
          <button className="sidebar-logout-btn" onClick={onLogout} title="Sign out">
            <i className="bi bi-box-arrow-right" />
          </button>
        </div>
      </div>
    </aside>
  )
}
