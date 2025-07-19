// ToDo管理ツールのメインJavaScriptファイル

class TodoApp {
    constructor() {
        this.todos = JSON.parse(localStorage.getItem('todos')) || [];
        this.currentFilter = 'all';
        this.init();
    }

    init() {
        this.bindEvents();
        this.render();
        this.updateStats();
    }

    bindEvents() {
        // フォーム送信イベント
        const todoForm = document.getElementById('todo-form');
        todoForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTodo();
        });

        // フィルターボタンイベント
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setFilter(btn.dataset.filter);
            });
        });

        // アクションボタンイベント
        document.getElementById('clear-completed').addEventListener('click', () => {
            this.clearCompleted();
        });

        document.getElementById('clear-all').addEventListener('click', () => {
            this.clearAll();
        });

        // 入力フィールドのEnterキーイベント
        const todoInput = document.getElementById('todo-input');
        todoInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTodo();
            }
        });
    }

    addTodo() {
        const input = document.getElementById('todo-input');
        const text = input.value.trim();

        if (text === '') {
            this.showNotification('タスクを入力してください', 'error');
            return;
        }

        if (text.length > 100) {
            this.showNotification('タスクは100文字以内で入力してください', 'error');
            return;
        }

        const todo = {
            id: Date.now(),
            text: text,
            completed: false,
            createdAt: new Date().toISOString()
        };

        this.todos.unshift(todo);
        this.saveTodos();
        this.render();
        this.updateStats();

        input.value = '';
        input.focus();

        this.showNotification('タスクを追加しました', 'success');
    }

    toggleTodo(id) {
        const todo = this.todos.find(t => t.id === id);
        if (todo) {
            todo.completed = !todo.completed;
            this.saveTodos();
            this.render();
            this.updateStats();

            const message = todo.completed ? 'タスクを完了しました' : 'タスクを未完了に戻しました';
            this.showNotification(message, 'info');
        }
    }

    deleteTodo(id) {
        const todo = this.todos.find(t => t.id === id);
        if (todo) {
            this.todos = this.todos.filter(t => t.id !== id);
            this.saveTodos();
            this.render();
            this.updateStats();
            this.showNotification('タスクを削除しました', 'info');
        }
    }

    clearCompleted() {
        const completedCount = this.todos.filter(t => t.completed).length;
        if (completedCount === 0) {
            this.showNotification('完了済みのタスクがありません', 'info');
            return;
        }

        if (confirm(`${completedCount}個の完了済みタスクを削除しますか？`)) {
            this.todos = this.todos.filter(t => !t.completed);
            this.saveTodos();
            this.render();
            this.updateStats();
            this.showNotification(`${completedCount}個のタスクを削除しました`, 'success');
        }
    }

    clearAll() {
        if (this.todos.length === 0) {
            this.showNotification('削除するタスクがありません', 'info');
            return;
        }

        if (confirm(`すべてのタスク（${this.todos.length}個）を削除しますか？`)) {
            this.todos = [];
            this.saveTodos();
            this.render();
            this.updateStats();
            this.showNotification('すべてのタスクを削除しました', 'success');
        }
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // フィルターボタンのアクティブ状態を更新
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`).classList.add('active');

        this.render();
    }

    getFilteredTodos() {
        switch (this.currentFilter) {
            case 'completed':
                return this.todos.filter(t => t.completed);
            case 'pending':
                return this.todos.filter(t => !t.completed);
            default:
                return this.todos;
        }
    }

    render() {
        const todoList = document.getElementById('todo-list');
        const emptyState = document.getElementById('empty-state');
        const filteredTodos = this.getFilteredTodos();

        if (filteredTodos.length === 0) {
            todoList.style.display = 'none';
            emptyState.style.display = 'block';
            
            // 空の状態メッセージをカスタマイズ
            const emptyMessage = document.querySelector('.empty-state p');
            const emptySubtitle = document.querySelector('.empty-subtitle');
            
            if (this.todos.length === 0) {
                emptyMessage.textContent = 'タスクがありません';
                emptySubtitle.textContent = '新しいタスクを追加してみましょう！';
            } else {
                emptyMessage.textContent = '該当するタスクがありません';
                emptySubtitle.textContent = 'フィルターを変更してみてください';
            }
        } else {
            todoList.style.display = 'block';
            emptyState.style.display = 'none';

            todoList.innerHTML = filteredTodos.map(todo => `
                <li class="todo-item ${todo.completed ? 'completed' : ''}" data-id="${todo.id}">
                    <div class="todo-checkbox ${todo.completed ? 'checked' : ''}" onclick="todoApp.toggleTodo(${todo.id})"></div>
                    <span class="todo-text">${this.escapeHtml(todo.text)}</span>
                    <button class="todo-delete" onclick="todoApp.deleteTodo(${todo.id})" title="削除">
                        <i class="fas fa-trash"></i>
                    </button>
                </li>
            `).join('');
        }
    }

    updateStats() {
        const totalTasks = this.todos.length;
        const completedTasks = this.todos.filter(t => t.completed).length;
        const pendingTasks = totalTasks - completedTasks;

        document.getElementById('total-tasks').textContent = totalTasks;
        document.getElementById('completed-tasks').textContent = completedTasks;
        document.getElementById('pending-tasks').textContent = pendingTasks;

        // 統計の色を動的に変更
        const totalElement = document.getElementById('total-tasks');
        const completedElement = document.getElementById('completed-tasks');
        const pendingElement = document.getElementById('pending-tasks');

        totalElement.style.color = totalTasks > 0 ? '#667eea' : '#999';
        completedElement.style.color = completedTasks > 0 ? '#28a745' : '#999';
        pendingElement.style.color = pendingTasks > 0 ? '#ffc107' : '#999';
    }

    saveTodos() {
        localStorage.setItem('todos', JSON.stringify(this.todos));
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showNotification(message, type = 'info') {
        // 既存の通知を削除
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        // 新しい通知を作成
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        // スタイルを追加
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getNotificationColor(type)};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            font-size: 0.9rem;
        `;

        document.body.appendChild(notification);

        // アニメーション
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // 自動削除
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }

    getNotificationColor(type) {
        switch (type) {
            case 'success': return '#28a745';
            case 'error': return '#dc3545';
            case 'warning': return '#ffc107';
            default: return '#17a2b8';
        }
    }
}

// アプリケーションの初期化
let todoApp;

document.addEventListener('DOMContentLoaded', () => {
    todoApp = new TodoApp();
});

// キーボードショートカット
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter でタスク追加
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        todoApp.addTodo();
    }
    
    // Escape でフィルターをリセット
    if (e.key === 'Escape') {
        todoApp.setFilter('all');
    }
});

// ページの可視性が変わった時の処理
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // ページが表示された時に統計を更新
        todoApp.updateStats();
    }
}); 