import { MESSAGE_TYPES, ERROR_MESSAGES } from './constants';

// Format timestamp to readable format
export const formatTimestamp = (timestamp) => {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return '';
    }
};

// Validate message input
export const validateMessage = (message) => {
    if (!message || !message.trim()) {
        return { isValid: false, error: ERROR_MESSAGES.INVALID_INPUT };
    }
    return { isValid: true, error: null };
};

// Format chat messages for display
export const formatChatMessage = (message, type = MESSAGE_TYPES.USER) => {
    return {
        id: generateMessageId(),
        type,
        content: message,
        timestamp: new Date().toISOString()
    };
};

// Generate unique message ID
export const generateMessageId = () => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Handle API errors
export const handleApiError = (error) => {
    if (!error.response) {
        return ERROR_MESSAGES.NETWORK_ERROR;
    }
    
    switch (error.response.status) {
        case 401:
            return ERROR_MESSAGES.SESSION_EXPIRED;
        case 500:
            return ERROR_MESSAGES.SERVER_ERROR;
        default:
            return error.response.data?.message || ERROR_MESSAGES.SERVER_ERROR;
    }
};

// Debounce function for API calls
export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Local storage helpers
export const storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },
    
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    }
};

// Truncate long text
export const truncateText = (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
};

// Copy text to clipboard
export const copyToClipboard = async (text) => {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        console.error('Failed to copy text:', error);
        return false;
    }
};

// Check if device is mobile
export const isMobile = () => {
    return window.innerWidth <= 768;
}; 