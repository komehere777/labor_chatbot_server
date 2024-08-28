
window.addEventListener('DOMContentLoaded', event => {
    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

    // Chatbot functionality
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');

    function addMessageToChat(message, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        if (isUser) {
            messageElement.classList.add('user-message');
        } else {
            messageElement.classList.add('ai-message');
        }
        messageElement.innerHTML = message;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    sendBtn.addEventListener('click', function() {
        const message = userInput.value;
        if (message.trim() === "") return;

        addMessageToChat(message, true);
        userInput.value = "";

        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            addMessageToChat(data.response);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    userInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendBtn.click();
        }
    });

    // Delete chat functionality
    const deleteButtons = document.querySelectorAll('.delete-chat');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();  // 이벤트 버블링 방지
            const historyId = this.getAttribute('data-history-id');
            if (confirm('정말로 이 채팅을 삭제하시겠습니까?')) {
                fetch(`/delete_chat_data/${historyId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            this.closest('.list-group-item').remove();
                            window.location.href = '/';
                        } else {
                            alert('채팅 삭제에 실패했습니다.');
                        }
                    });
            }
        });
    });
});
