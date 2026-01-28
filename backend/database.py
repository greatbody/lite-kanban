import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple

DB_PATH = 'kanban.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'backlog',
            priority TEXT DEFAULT 'medium',
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            planned_date DATE,
            completed_date DATE,
            total_time_spent INTEGER DEFAULT 0
        )
    ''')
    
    # Status history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    # Time tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            started_at TIMESTAMP NOT NULL,
            ended_at TIMESTAMP,
            duration_minutes INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def dict_from_row(row) -> Dict:
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    d = dict(row)
    # Parse tags JSON
    if 'tags' in d and d['tags']:
        d['tags'] = json.loads(d['tags'])
    else:
        d['tags'] = []
    return d

def get_all_tasks() -> List[Dict]:
    """Get all tasks"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    tasks = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id: int) -> Optional[Dict]:
    """Get task by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = dict_from_row(cursor.fetchone())
    conn.close()
    return task

def create_task(title: str, description: str = '', priority: str = 'medium', tags: List[str] = None) -> int:
    """Create a new task"""
    conn = get_db()
    cursor = conn.cursor()
    
    tags_json = json.dumps(tags if tags else [])
    
    cursor.execute('''
        INSERT INTO tasks (title, description, priority, tags, status)
        VALUES (?, ?, ?, ?, 'backlog')
    ''', (title, description, priority, tags_json))
    
    task_id = cursor.lastrowid
    
    # Record initial status
    cursor.execute('''
        INSERT INTO status_history (task_id, from_status, to_status, reason)
        VALUES (?, NULL, 'backlog', '创建任务')
    ''', (task_id,))
    
    conn.commit()
    conn.close()
    return task_id

def update_task(task_id: int, title: str = None, description: str = None, 
                priority: str = None, tags: List[str] = None) -> bool:
    """Update task details (not status)"""
    conn = get_db()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if title is not None:
        updates.append('title = ?')
        params.append(title)
    if description is not None:
        updates.append('description = ?')
        params.append(description)
    if priority is not None:
        updates.append('priority = ?')
        params.append(priority)
    if tags is not None:
        updates.append('tags = ?')
        params.append(json.dumps(tags))
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()
    return True

def move_task(task_id: int, to_status: str, reason: str = '') -> Tuple[bool, str]:
    """
    Move task to new status with business logic enforcement
    Returns: (success, message)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current task
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return False, '任务不存在'
    
    from_status = task['status']
    
    # Validate transition
    valid_transitions = {
        'backlog': ['planned'],
        'planned': ['in_progress', 'pending_short', 'pending_long'],
        'in_progress': ['done', 'pending_short', 'pending_long'],
        'pending_short': ['planned', 'in_progress', 'pending_long'],
        'pending_long': ['planned']
    }
    
    if to_status not in valid_transitions.get(from_status, []):
        conn.close()
        return False, f'不允许从 {from_status} 移动到 {to_status}'
    
    # Handle In Progress uniqueness
    if to_status == 'in_progress':
        cursor.execute('SELECT id FROM tasks WHERE status = "in_progress" AND id != ?', (task_id,))
        current_in_progress = cursor.fetchone()
        
        if current_in_progress:
            # Move current in_progress task to pending_short
            old_task_id = current_in_progress['id']
            cursor.execute('UPDATE tasks SET status = "pending_short", updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                          (old_task_id,))
            cursor.execute('''
                INSERT INTO status_history (task_id, from_status, to_status, reason)
                VALUES (?, 'in_progress', 'pending_short', '被新任务挤出')
            ''', (old_task_id,))
            
            # End time tracking for old task
            _end_time_tracking(cursor, old_task_id)
    
    # Handle time tracking
    if from_status == 'in_progress':
        # Ending in_progress, stop timer
        _end_time_tracking(cursor, task_id)
    
    if to_status == 'in_progress':
        # Starting in_progress, start timer
        cursor.execute('''
            INSERT INTO time_tracking (task_id, started_at)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (task_id,))
    
    # Update task status
    update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
    params = [to_status]
    
    # Set planned_date if moving to planned for first time
    if to_status == 'planned' and not task['planned_date']:
        update_fields.append('planned_date = ?')
        params.append(date.today().isoformat())
    
    # Set completed_date if moving to done
    if to_status == 'done':
        update_fields.append('completed_date = ?')
        params.append(date.today().isoformat())
    
    params.append(task_id)
    cursor.execute(f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?", params)
    
    # Record status change
    cursor.execute('''
        INSERT INTO status_history (task_id, from_status, to_status, reason)
        VALUES (?, ?, ?, ?)
    ''', (task_id, from_status, to_status, reason or ''))
    
    conn.commit()
    conn.close()
    return True, '成功'

def _end_time_tracking(cursor, task_id: int):
    """End current time tracking session and update total time"""
    # Get active tracking session
    cursor.execute('''
        SELECT id, started_at FROM time_tracking 
        WHERE task_id = ? AND ended_at IS NULL
        ORDER BY started_at DESC LIMIT 1
    ''', (task_id,))
    
    tracking = cursor.fetchone()
    if tracking:
        # SQLite CURRENT_TIMESTAMP returns UTC time, so we must use utcnow() for consistency
        started_at = datetime.fromisoformat(tracking['started_at'])
        ended_at = datetime.utcnow()
        
        # Calculate duration in minutes (minimum 1 minute)
        duration = (ended_at - started_at).total_seconds() / 60
        duration_minutes = max(1, int(duration + 0.5))  # Round up
        
        # Update tracking record
        cursor.execute('''
            UPDATE time_tracking 
            SET ended_at = ?, duration_minutes = ?
            WHERE id = ?
        ''', (ended_at.isoformat(), duration_minutes, tracking['id']))
        
        # Update task total time
        cursor.execute('''
            UPDATE tasks 
            SET total_time_spent = total_time_spent + ?
            WHERE id = ?
        ''', (duration_minutes, task_id))

def delete_task(task_id: int) -> bool:
    """Delete a task"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if task is in in_progress, need to end tracking
    cursor.execute('SELECT status FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    if task and task['status'] == 'in_progress':
        _end_time_tracking(cursor, task_id)
    
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_status_history(task_id: int) -> List[Dict]:
    """Get status change history for a task"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM status_history 
        WHERE task_id = ? 
        ORDER BY changed_at DESC
    ''', (task_id,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def get_time_tracking(task_id: int) -> List[Dict]:
    """Get time tracking records for a task"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM time_tracking 
        WHERE task_id = ? 
        ORDER BY started_at DESC
    ''', (task_id,))
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records

def process_daily_tasks():
    """Process tasks from previous day - move incomplete tasks to planned"""
    conn = get_db()
    cursor = conn.cursor()
    
    today = date.today().isoformat()
    
    # Find tasks that need processing:
    # - In planned/in_progress/pending_short
    # - planned_date is not today (or NULL for in_progress/pending_short)
    cursor.execute('''
        SELECT id, status FROM tasks 
        WHERE status IN ('planned', 'in_progress', 'pending_short')
        AND (planned_date IS NULL OR planned_date < ?)
    ''', (today,))
    
    tasks_to_process = cursor.fetchall()
    processed_count = 0
    
    for task in tasks_to_process:
        task_id = task['id']
        from_status = task['status']
        
        # End time tracking if in_progress
        if from_status == 'in_progress':
            _end_time_tracking(cursor, task_id)
        
        # Move to planned
        cursor.execute('''
            UPDATE tasks 
            SET status = 'planned', planned_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (today, task_id))
        
        # Record status change
        cursor.execute('''
            INSERT INTO status_history (task_id, from_status, to_status, reason)
            VALUES (?, ?, 'planned', '昨日未完成')
        ''', (task_id, from_status))
        
        processed_count += 1
    
    conn.commit()
    conn.close()
    
    return processed_count
