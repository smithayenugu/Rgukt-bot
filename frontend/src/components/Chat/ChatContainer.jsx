import { 
    formatChatMessage, 
    handleApiError, 
    storage 
} from '../../utils/helpers';
import { 
    MESSAGE_TYPES, 
    STORAGE_KEYS, 
    ERROR_MESSAGES 
} from '../../utils/constants';

const ChatContainer = () => {
    // Using the utilities
    const sessionId = storage.get(STORAGE_KEYS.SESSION_ID);
    
    const handleNewMessage = (message) => {
        const formattedMessage = formatChatMessage(message, MESSAGE_TYPES.USER);
        // ... rest of the code
    };
    
    const handleError = (error) => {
        const errorMessage = handleApiError(error);
        // ... error handling
    };
    
    // ... rest of the component
}; 