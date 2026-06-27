import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Load saved preference from localStorage, default to false (light mode)
    const saved = localStorage.getItem('rgukt-dark-mode');
    const isDark = saved ? JSON.parse(saved) : false;
    // Apply class synchronously to prevent flash
    if (isDark) {
      document.documentElement.classList.add('dark-mode');
    }
    return isDark;
  });

  useEffect(() => {
    // Save to localStorage whenever it changes
    localStorage.setItem('rgukt-dark-mode', JSON.stringify(isDarkMode));
    // Toggle dark class on root element for scrollbar CSS
    if (isDarkMode) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}; 