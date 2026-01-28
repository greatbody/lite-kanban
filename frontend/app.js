const { createApp } = Vue;

const API_BASE = '/api';

createApp({
    data() {
        return {
            tasks: [],
            columns: [
                { id: 'backlog', title: 'Backlog' },
                { id: 'planned', title: 'Planned' },
                { id: 'in_progress', title: 'In Progress' },
                { id: 'pending_short', title: 'Pending (Short)' },
                { id: 'pending_long', title: 'Pending (Long)' },
                { id: 'done', title: 'Done' }
            ],
            showModal: false,
            isEditing: false,
            currentTask: this.getEmptyTask(),
            newTag: '',
            taskHistory: [],
            columnRefs: {}
        };
    },
    mounted() {
        this.loadTasks();
        this.initSortable();
    },
    methods: {
        getEmptyTask() {
            return {
                title: '',
                description: '',
                priority: 'medium',
                tags: []
            };
        },
        
        async loadTasks() {
            try {
                const response = await fetch(`${API_BASE}/tasks`);
                this.tasks = await response.json();
            } catch (error) {
                console.error('加载任务失败:', error);
                alert('加载任务失败，请确保后端服务已启动');
            }
        },
        
        getTasksByStatus(status) {
            return this.tasks.filter(task => task.status === status);
        },
        
        setColumnRef(status, el) {
            if (el) {
                this.columnRefs[status] = el;
            }
        },
        
        initSortable() {
            this.$nextTick(() => {
                Object.keys(this.columnRefs).forEach(status => {
                    const el = this.columnRefs[status];
                    if (el) {
                        new Sortable(el, {
                            group: 'kanban',
                            animation: 150,
                            ghostClass: 'sortable-ghost',
                            dragClass: 'sortable-drag',
                            onEnd: (evt) => {
                                const taskId = parseInt(evt.item.dataset.id);
                                const toStatus = evt.to.dataset.status;
                                this.moveTask(taskId, toStatus);
                            }
                        });
                    }
                });
            });
        },
        
        async moveTask(taskId, toStatus) {
            try {
                const response = await fetch(`${API_BASE}/tasks/${taskId}/move`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ to_status: toStatus })
                });
                
                if (response.ok) {
                    await this.loadTasks();
                } else {
                    const error = await response.json();
                    alert(error.error || '移动任务失败');
                    await this.loadTasks(); // Reload to reset UI
                }
            } catch (error) {
                console.error('移动任务失败:', error);
                alert('移动任务失败');
                await this.loadTasks();
            }
        },
        
        showCreateModal() {
            this.isEditing = false;
            this.currentTask = this.getEmptyTask();
            this.taskHistory = [];
            this.showModal = true;
        },
        
        async showEditModal(task) {
            this.isEditing = true;
            this.currentTask = {
                id: task.id,
                title: task.title,
                description: task.description || '',
                priority: task.priority,
                tags: [...task.tags]
            };
            
            // Load history
            try {
                const response = await fetch(`${API_BASE}/tasks/${task.id}/history`);
                this.taskHistory = await response.json();
            } catch (error) {
                console.error('加载历史失败:', error);
                this.taskHistory = [];
            }
            
            this.showModal = true;
        },
        
        closeModal() {
            this.showModal = false;
            this.currentTask = this.getEmptyTask();
            this.newTag = '';
            this.taskHistory = [];
        },
        
        async saveTask() {
            if (!this.currentTask.title.trim()) {
                alert('请输入任务标题');
                return;
            }
            
            try {
                if (this.isEditing) {
                    // Update task
                    const response = await fetch(`${API_BASE}/tasks/${this.currentTask.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.currentTask)
                    });
                    
                    if (response.ok) {
                        await this.loadTasks();
                        this.closeModal();
                    } else {
                        const error = await response.json();
                        alert(error.error || '更新任务失败');
                    }
                } else {
                    // Create task
                    const response = await fetch(`${API_BASE}/tasks`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.currentTask)
                    });
                    
                    if (response.ok) {
                        await this.loadTasks();
                        this.closeModal();
                    } else {
                        const error = await response.json();
                        alert(error.error || '创建任务失败');
                    }
                }
            } catch (error) {
                console.error('保存任务失败:', error);
                alert('保存任务失败');
            }
        },
        
        async deleteTask(taskId) {
            if (!confirm('确定要删除这个任务吗？')) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    await this.loadTasks();
                } else {
                    const error = await response.json();
                    alert(error.error || '删除任务失败');
                }
            } catch (error) {
                console.error('删除任务失败:', error);
                alert('删除任务失败');
            }
        },
        
        addTag() {
            const tag = this.newTag.trim();
            if (tag && !this.currentTask.tags.includes(tag)) {
                this.currentTask.tags.push(tag);
                this.newTag = '';
            }
        },
        
        removeTag(index) {
            this.currentTask.tags.splice(index, 1);
        },
        
        async processDailyTasks() {
            if (!confirm('确定要处理昨日未完成的任务吗？这将把它们移动到今日计划中。')) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/daily-process`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    alert(result.message);
                    await this.loadTasks();
                } else {
                    alert('处理失败');
                }
            } catch (error) {
                console.error('处理失败:', error);
                alert('处理失败');
            }
        },
        
        formatTime(minutes) {
            if (minutes < 60) {
                return `${minutes}分钟`;
            }
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`;
        },
        
        formatDateTime(dateTimeStr) {
            const date = new Date(dateTimeStr);
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${month}-${day} ${hours}:${minutes}`;
        },
        
        getStatusName(status) {
            const statusMap = {
                'backlog': 'Backlog',
                'planned': 'Planned',
                'in_progress': 'In Progress',
                'pending_short': 'Pending (Short)',
                'pending_long': 'Pending (Long)',
                'done': 'Done'
            };
            return statusMap[status] || status;
        }
    }
}).mount('#app');
