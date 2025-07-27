import { useState, useEffect } from 'react';
import { chatService } from '../services/chatService';

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const sendMessage = async (message) => {
        setLoading(true);
        setError(null);
        
        try {
            // Add user message to chat history
            const userMessage = { role: 'user', content: message };
            const updatedHistory = [...messages, userMessage];
            
            // Send message with chat history
            const response = await chatService.sendMessage(message, updatedHistory);
            
            // Update messages with the response from the API
            setMessages(response.chat_history || []);
        } catch (err) {
            setError(err.message || 'Failed to send message');
            console.error('Chat error:', err);
        } finally {
            setLoading(false);
        }
    };

    const clearHistory = async () => {
        try {
            await chatService.clearHistory();
            setMessages([]);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to clear history');
            console.error('Clear history error:', err);
        }
    };

    return { 
        messages, 
        loading, 
        error, 
        sendMessage, 
        clearHistory 
    };
}; 