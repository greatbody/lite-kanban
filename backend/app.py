from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import database as db
import os

# Get the project root directory (parent of backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)  # Enable CORS for local development

# Initialize database on startup
db.init_db()

@app.route('/')
def index():
    """Serve the frontend index.html"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    tasks = db.get_all_tasks()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': '标题不能为空'}), 400
    
    description = data.get('description', '')
    priority = data.get('priority', 'medium')
    tags = data.get('tags', [])
    
    task_id = db.create_task(title, description, priority, tags)
    task = db.get_task_by_id(task_id)
    
    return jsonify(task), 201

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task"""
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(task)

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update task details (not status)"""
    data = request.json
    
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    title = data.get('title')
    description = data.get('description')
    priority = data.get('priority')
    tags = data.get('tags')
    
    db.update_task(task_id, title, description, priority, tags)
    updated_task = db.get_task_by_id(task_id)
    
    return jsonify(updated_task)

@app.route('/api/tasks/<int:task_id>/move', methods=['PUT'])
def move_task(task_id):
    """Move task to a new status"""
    data = request.json
    
    to_status = data.get('to_status')
    reason = data.get('reason', '')
    
    if not to_status:
        return jsonify({'error': '目标状态不能为空'}), 400
    
    success, message = db.move_task(task_id, to_status, reason)
    
    if success:
        task = db.get_task_by_id(task_id)
        return jsonify(task)
    else:
        return jsonify({'error': message}), 400

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    success = db.delete_task(task_id)
    
    if success:
        return jsonify({'message': '删除成功'})
    else:
        return jsonify({'error': '任务不存在'}), 404

@app.route('/api/tasks/<int:task_id>/history', methods=['GET'])
def get_task_history(task_id):
    """Get status change history for a task"""
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    history = db.get_status_history(task_id)
    return jsonify(history)

@app.route('/api/tasks/<int:task_id>/time-tracking', methods=['GET'])
def get_task_time_tracking(task_id):
    """Get time tracking records for a task"""
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    records = db.get_time_tracking(task_id)
    return jsonify(records)

@app.route('/api/daily-process', methods=['POST'])
def daily_process():
    """Process daily tasks - move incomplete tasks to planned"""
    count = db.process_daily_tasks()
    return jsonify({
        'message': f'处理完成，移动了 {count} 个任务到今日计划',
        'processed_count': count
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('=' * 50)
    print('🚀 Starting Lite Kanban...')
    print('=' * 50)
    print(f'Frontend: http://localhost:5001')
    print(f'API:      http://localhost:5001/api')
    print(f'Frontend files: {FRONTEND_DIR}')
    print('=' * 50)
    print('Press Ctrl+C to stop')
    print()
    app.run(debug=True, host='0.0.0.0', port=5001)
