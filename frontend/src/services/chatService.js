import api from './api';

export const chatService = {
    async sendMessage(message, chatHistory = []) {
        try {
            const response = await api.post('/api/chat', {
                text: message,
                chat_history: chatHistory
            });
            return response.data;
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    },

    async clearHistory() {
        try {
            const response = await api.post('/api/clear-history');
            return response.data;
        } catch (error) {
            console.error('Error clearing chat history:', error);
            throw error;
        }
    }
}; 