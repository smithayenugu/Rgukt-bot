// API endpoints
export const API_ENDPOINTS = {
    CHAT: '/api/chat',
    CHAT_HISTORY: '/api/chat/history',
    BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
};

// Message types
export const MESSAGE_TYPES = {
    USER: 'user',
    BOT: 'bot',
    ERROR: 'error',
    SYSTEM: 'system'
};

// Local storage keys
export const STORAGE_KEYS = {
    SESSION_ID: 'chatSessionId',
    USER_PREFERENCES: 'userPreferences',
    THEME: 'theme'
};

// UI Constants
export const UI_CONSTANTS = {
    MAX_MESSAGE_LENGTH: 500,
    MESSAGE_TIMEOUT: 30000, // 30 seconds
    TYPING_INDICATOR_DELAY: 1000,
    MAX_RETRIES: 3
};

// Error messages
export const ERROR_MESSAGES = {
    NETWORK_ERROR: 'Network error. Please check your connection.',
    SERVER_ERROR: 'Server error. Please try again later.',
    INVALID_INPUT: 'Please enter a valid message.',
    SESSION_EXPIRED: 'Your session has expired. Please refresh the page.'
}; 