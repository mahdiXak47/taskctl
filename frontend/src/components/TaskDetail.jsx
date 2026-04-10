import './TaskDetail.css'

const STATUS_META = {
  not_started:       { label: 'Not Started',        icon: 'bi-hourglass',               cls: 'status-not-started' },
  in_progress:       { label: 'In Progress',         icon: 'bi-play-circle-fill',        cls: 'status-in-progress' },
  breached_deadline: { label: 'Breached Deadline',   icon: 'bi-exclamation-circle-fill', cls: 'status-breached' },
  done_intime:       { label: 'Done',                icon: 'bi-check-circle-fill',       cls: 'status-done' },
  done_but_breached: { label: 'Done (Late)',          icon: 'bi-check-circle',            cls: 'status-done-but-breached' },
}

function MetaRow({ icon, label, value }) {
  if (!value) return null
  return (
    <div className="detail-meta-row">
      <span className="detail-meta-label">
        <i className={`bi ${icon}`} />
        {label}
      </span>
      <span className="detail-meta-value">{value}</span>
    </div>
  )
}

function CommentBubble({ comment }) {
  const text    = typeof comment === 'string' ? comment : comment.text
  const date    = typeof comment === 'string' ? null    : comment.created_at
  return (
    <div className="comment-bubble">
      <div className="comment-bubble-header">
        <i className="bi bi-person-circle comment-avatar" />
        {date && <span className="comment-date">{date}</span>}
      </div>
      <p className="comment-text">{text}</p>
    </div>
  )
}

export default function TaskDetail({ task, onClose }) {
  const meta = STATUS_META[task.status] ?? { label: task.status, icon: 'bi-circle', cls: '' }

  return (
    <div className="task-detail-pane">
      {/* ── Header ── */}
      <header className="detail-header">
        <button className="detail-back-btn" onClick={onClose}>
          <i className="bi bi-arrow-left" />
          Back
        </button>
        <span className="detail-task-id">#{task.task_id}</span>
      </header>

      {/* ── Title bar with inline status ── */}
      <div className="detail-title-bar">
        <span className={`status-badge-lg ${meta.cls}`}>
          <i className={`bi ${meta.icon}`} />
          {meta.label}
        </span>
        <h1 className="detail-title">{task.title}</h1>
      </div>

      {/* ── Body: two columns ── */}
      <div className="detail-body">

        {/* Left: description + comments */}
        <div className="detail-main">
          <section className="detail-section">
            <h2 className="detail-section-heading">
              <i className="bi bi-text-paragraph" />
              Description
            </h2>
            {task.description
              ? <p className="detail-description">{task.description}</p>
              : <p className="detail-empty-hint">No description provided.</p>
            }
          </section>

          <section className="detail-section">
            <h2 className="detail-section-heading">
              <i className="bi bi-chat-left-text" />
              Comments
              {task.comments?.length > 0 && (
                <span className="detail-comment-count">{task.comments.length}</span>
              )}
            </h2>
            {(!task.comments || task.comments.length === 0)
              ? <p className="detail-empty-hint">No comments yet. Use <code>taskctl comment {task.task_id} -m "..."</code></p>
              : (
                <div className="comment-list">
                  {task.comments.map((c, i) => (
                    <CommentBubble key={i} comment={c} />
                  ))}
                </div>
              )
            }
          </section>
        </div>

        {/* Right: metadata */}
        <aside className="detail-sidebar">
          <h2 className="detail-section-heading">
            <i className="bi bi-info-circle" />
            Details
          </h2>
          <div className="detail-meta-grid">
            <MetaRow icon="bi-tag"              label="Task ID"       value={task.task_id} />
            <MetaRow icon="bi-clock"            label="ETA"           value={task.eta} />
            <MetaRow icon="bi-calendar3"        label="Created"       value={task.created_time} />
            <MetaRow icon="bi-play-circle"      label="Started"       value={task.started_time} />
            <MetaRow icon="bi-calendar-check"   label="Expected End"  value={task.expected_end_time} />
            <MetaRow icon="bi-check2-circle"    label="Finished"      value={task.end_time} />
          </div>
        </aside>

      </div>
    </div>
  )
}
