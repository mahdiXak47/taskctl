import './TaskCard.css'

const STATUS_META = {
  not_started:       { label: 'Not Started',       icon: 'bi-hourglass',               cls: 'status-not-started' },
  in_progress:       { label: 'In Progress',        icon: 'bi-play-circle-fill',        cls: 'status-in-progress' },
  breached_deadline: { label: 'Breached Deadline',  icon: 'bi-exclamation-circle-fill', cls: 'status-breached' },
  done_intime:       { label: 'Done',               icon: 'bi-check-circle-fill',       cls: 'status-done' },
  done_but_breached: { label: 'Done (Late)',         icon: 'bi-check-circle',            cls: 'status-done-but-breached' },
}

export default function TaskCard({ task, onClick }) {
  const meta = STATUS_META[task.status] ?? { label: task.status, icon: 'bi-circle', cls: '' }

  return (
    <article className="task-card" onClick={onClick} role="button" tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick?.()}>
      <div className="task-card-top">
        <span className="task-id">#{task.task_id}</span>
        <span className={`status-badge ${meta.cls}`}>
          <i className={`bi ${meta.icon}`} />
          {meta.label}
        </span>
      </div>

      <h3 className="task-title">{task.title}</h3>

      {task.description && (
        <p className="task-description">{task.description}</p>
      )}

      <div className="task-card-footer">
        {task.eta && (
          <span className="task-meta-pill">
            <i className="bi bi-clock" />
            {task.eta}
          </span>
        )}
        {task.created_time && (
          <span className="task-meta-pill">
            <i className="bi bi-calendar3" />
            {task.created_time}
          </span>
        )}
        {task.comments?.length > 0 && (
          <span className="task-meta-pill">
            <i className="bi bi-chat-left-text" />
            {task.comments.length} comment{task.comments.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </article>
  )
}
