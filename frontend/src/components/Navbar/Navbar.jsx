import React, { useRef, useEffect, useState } from 'react';
import { TbLayoutSidebarLeftExpand } from 'react-icons/tb';
import { MdAdd } from 'react-icons/md';
import { useTheme } from '../../context/ThemeContext';
import lightlogo from '../../assets/lightlogo.png';
import darklogo from '../../assets/darklogo.png';
import './navbar.css';

const Navbar = () => {
  const sidebarRef = useRef();
  const { isDarkMode, toggleTheme } = useTheme();
  const [logoLoaded, setLogoLoaded] = useState(false);

  // Preload images
  useEffect(() => {
    const preloadImages = () => {
      const lightImg = new Image();
      const darkImg = new Image();
      lightImg.src = lightlogo;
      darkImg.src = darklogo;
      
      Promise.all([
        new Promise(resolve => { lightImg.onload = resolve; }),
        new Promise(resolve => { darkImg.onload = resolve; })
      ]).then(() => {
        setLogoLoaded(true);
      });
    };

    preloadImages();
  }, []);

  const toggleSidebar = () => {
    sidebarRef.current.classList.toggle('-translate-x-full');
  };

  const questions = [
    "How do I apply for campus admission?",
    "What documents are required for admission?",
    "How can I prepare for campus placement?",
    "Where can I find the campus map?"
  ];

  return (
    <nav className="absolute top-0 left-0 z-20 w-full font-poppins">
      <div className="p-4">
        <button 
          onClick={toggleSidebar} 
          className={`p-2 rounded-lg transition-colors flex items-center justify-center
            ${isDarkMode 
              ? 'text-white hover:bg-[#2d2d30]' 
              : 'text-gray-700 hover:bg-gray-100'}`}
        >
          <TbLayoutSidebarLeftExpand className="text-2xl" />
        </button>
      </div>

      <div 
        ref={sidebarRef}
        className={`fixed top-0 left-0 w-[260px] h-full -translate-x-full transition-all duration-300 ease-in-out
          ${isDarkMode 
            ? 'bg-[#202123] border-r border-[#2d2d30] text-white' 
            : 'bg-white border-r border-gray-200'}`}
      >
        <div className="flex flex-col h-full p-2">
          <div className="flex items-center justify-between p-2">
            <button 
              onClick={toggleSidebar} 
              className={`p-2 rounded-lg transition-colors flex items-center justify-center
                ${isDarkMode 
                  ? 'text-white hover:bg-[#2d2d30]' 
                  : 'text-gray-700 hover:bg-gray-100'}`}
            >
              <TbLayoutSidebarLeftExpand className="text-2xl" />
            </button>
            
            <label className="switch">
              <input 
                type="checkbox" 
                checked={isDarkMode}
                onChange={toggleTheme}
              />
              <span className="slider"></span>
            </label>
          </div>

          {/* Logo with fallback and error handling */}
          <div className="flex justify-center h-20 my-2 relative">
            {logoLoaded && (
              <img 
                src={isDarkMode ? lightlogo : darklogo}
                alt="Logo" 
                className="h-full w-auto object-contain transition-opacity duration-300"
                onError={(e) => {
                  e.target.style.opacity = 0;
                  console.error('Logo failed to load');
                }}
                style={{ opacity: logoLoaded ? 1 : 0 }}
              />
            )}
          </div>

          <button className={`flex items-center gap-2 p-3 rounded-lg transition-all duration-200 mx-2 mb-4
            ${isDarkMode 
              ? 'bg-[#2d2d30] hover:bg-[#4d4d4f] text-white' 
              : 'bg-white hover:bg-gray-100 text-gray-800 border border-gray-200'}`}
          >
            <MdAdd className="text-xl" />
            <span className="font-medium">New Chat</span>
          </button>

          <div className="px-2">
            <h3 className={`text-base font-semibold mb-2 px-2
              ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}
            >
              Common Questions
            </h3>
            <div className="flex flex-col gap-1">
              {questions.map((question, index) => (
                <button 
                  key={index}
                  className={`p-3 rounded-lg text-sm text-left transition-colors w-full
                    ${isDarkMode 
                      ? 'hover:bg-[#2d2d30] text-gray-200' 
                      : 'hover:bg-gray-100 text-gray-800'}`}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
