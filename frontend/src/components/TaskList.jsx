import TaskCard from './TaskCard'
import './TaskList.css'

const DURATION_OPTIONS = [
  { label: 'Today',   value: 1 },
  { label: '7 days',  value: 7 },
  { label: '30 days', value: 30 },
]

export default function TaskList({ tasks, loading, error, days, setDays, onRefresh, onTaskClick }) {
  return (
    <main className="task-list-pane">
      <header className="task-list-header">
        <div className="task-list-header-left">
          <h1 className="task-list-heading">Tasks</h1>
          {!loading && (
            <span className="task-count">{tasks.length} task{tasks.length !== 1 ? 's' : ''}</span>
          )}
        </div>

        <div className="task-list-header-right">
          <div className="duration-selector">
            {DURATION_OPTIONS.map(opt => (
              <button
                key={opt.value}
                className={`dur-btn ${days === opt.value ? 'active' : ''}`}
                onClick={() => setDays(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <button className="refresh-btn" onClick={onRefresh} title="Refresh">
            <i className="bi bi-arrow-clockwise" />
          </button>
        </div>
      </header>

      <div className="task-list-body">
        {loading && (
          <div className="task-list-state">
            <i className="bi bi-arrow-repeat task-list-state-icon spinning" />
            <p>Loading tasks…</p>
          </div>
        )}

        {!loading && error && (
          <div className="task-list-state task-list-error">
            <i className="bi bi-exclamation-triangle task-list-state-icon" />
            <p>{error}</p>
            <p className="task-list-state-hint">Is <code>taskctl serve</code> running?</p>
          </div>
        )}

        {!loading && !error && tasks.length === 0 && (
          <div className="task-list-state">
            <i className="bi bi-inbox task-list-state-icon" />
            <p>No tasks found for this period.</p>
          </div>
        )}

        {!loading && !error && tasks.length > 0 && (
          <div className="task-grid">
            {tasks.map(task => (
              <TaskCard key={task.task_id} task={task} onClick={() => onTaskClick(task)} />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
