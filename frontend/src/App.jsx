import React, { useState, useRef, useEffect } from "react";
import darkLogo from "../src/assets/darklogo.png";
import lightLogo from "../src/assets/lightlogo.png";
import botIcon from "../src/assets/icon.png";
import { useTheme } from "./pages/ThemeContext";
import {
  FaGraduationCap,
  FaAward,
  FaBuilding,
  FaCreditCard,
} from "react-icons/fa";

// Strip inline style attributes from HTML so theme colors cascade from CSS
function stripInlineStyles(html) {
  return html.replace(/\s+style="[^"]*"/gi, '');
}


function App() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatting, setIsChatting] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessionId] = useState(Date.now().toString()); // Unique session ID
  const [isLoading, setIsLoading] = useState(false); // Loading state for responses
  const chatEndRef = useRef(null);
  const { isDarkMode, toggleTheme } = useTheme();

  // Auto-scroll to bottom when chatHistory changes
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [chatHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userMessage = message;
    setMessage("");

    // Immediately show user message on screen
    setIsChatting(true);
    setIsLoading(true);
    setChatHistory((prev) => [
      ...prev,
      { type: "user", text: userMessage },
      { type: "bot", text: "loading" }, // placeholder for loading indicator
    ]);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, text: userMessage, chat_history: chatHistory }),
      });

      const data = await response.json();

      // Replace the loading placeholder with actual response
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { type: "bot", text: data.response };
        return updated;
      });
    } catch (error) {
      console.error("Error:", error);
      // Replace loading with error message
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { type: "bot", text: "Sorry, I encountered an error. Please try again." };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const cards = [
    {
      icon: <FaGraduationCap className="text-[#8BB9FE]" />,
      title: "Explore the",
      subtitle: "Eligibility Criteria",
      description: "for B.Tech Programs",
      borderColor: "border-blue-100",
      bgColor: "bg-blue-50",
    },
    {
      icon: <FaAward className="text-[#98E9AB]" />,
      title: "Explore",
      subtitle: "Scholarship Options",
      description: "and Financial Aid",
      borderColor: "border-green-100",
      bgColor: "bg-green-50",
    },
    {
      icon: <FaBuilding className="text-[#E5A0FF]" />,
      title: "Explore Campus",
      subtitle: "Recruitment",
      description: "Opportunities",
      borderColor: "border-pink-100",
      bgColor: "bg-pink-50",
    },
    {
      icon: <FaCreditCard className="text-[#FFE7A0]" />,
      title: "Learn About",
      subtitle: "Tuition Fees and",
      description: "Payment Methods",
      borderColor: "border-yellow-100",
      bgColor: "bg-yellow-50",
    },
  ];

  const commonQuestions = [
    "How do I apply for campus admission?",
    "What documents are required for admission?",
    "How can I prepare for campus placement?",
    "Where can I find the campus map?",
  ];

  // Function to handle new chat
  const handleNewChat = () => {
    // Clear chat history
    setChatHistory([]);
    // Reset message input
    setMessage("");
    // Set chatting state to false to show initial UI
    setIsChatting(false);
  };

  // Define card questions
  const cardQuestions = {
    eligibility:
      "What are the eligibility criteria and requirements for B.Tech programs?",
    scholarship:
      "What scholarship options and financial aid are available for students?",
    recruitment:
      "Tell me about campus recruitment opportunities and placement services.",
    fees: "What are the tuition fees and available payment methods?",
  };

  // Handle card click
  const handleCardClick = async (question) => {
    if (isLoading) return;
    setIsChatting(true);
    setMessage("");
    setIsLoading(true);

    // Immediately show user question and loading indicator
    setChatHistory((prev) => [
      ...prev,
      {
        type: "user",
        text: question,
      },
      { type: "bot", text: "loading" },
    ]);

    try {
      // Make API call to get response
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, text: question }),
      });

      const data = await response.json();

      // Replace loading placeholder with actual response
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { type: "bot", text: data.response };
        return updated;
      });
    } catch (error) {
      console.error("Error:", error);
      setChatHistory((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { type: "bot", text: "Sorry, I encountered an error. Please try again." };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className={`flex min-h-screen relative ${isDarkMode ? 'bg-[#202123] text-gray-200' : 'bg-white text-black'}`}>
      {/* Toggle Button */}
      <button
        onClick={toggleSidebar}
        className={`fixed top-4 left-4 z-50 p-2 rounded-lg shadow-md transition-all duration-300 ${
          isDarkMode ? 'bg-[#2d2d30] hover:bg-[#4d4d4f] text-gray-300' : 'bg-white hover:bg-gray-50 text-gray-600'
        }`}
        aria-label="Toggle Sidebar"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      {/* Sidebar */}
      <div
        className={`fixed md:relative ${
          isSidebarOpen ? "w-[300px]" : "w-0"
        } transition-all duration-300 border-r overflow-hidden h-full z-40 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        } ${isDarkMode ? 'bg-[#202123] border-[#2d2d30]' : 'bg-white border-gray-200'}`}
      >
        {/* Sidebar content */}
        <div className="p-6 pt-16 flex flex-col h-full">
          {/* Logo */}
          <div className="mb-6 flex justify-center items-center">
            <img src={isDarkMode ? lightLogo : darkLogo} alt="RGU Logo" className="h-20 w-auto" />
          </div>

          {/* Theme Toggle */}
          <div className="flex items-center justify-between mb-4 px-2">
            <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {isDarkMode ? 'Dark Mode' : 'Light Mode'}
            </span>
            <button
              onClick={toggleTheme}
              className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
                isDarkMode ? 'bg-[#4d4d4f]' : 'bg-gray-300'
              }`}
            >
              <div
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-md transition-transform duration-300 flex items-center justify-center text-xs ${
                  isDarkMode ? 'translate-x-6' : 'translate-x-0.5'
                } ${isDarkMode ? 'ml-0.5' : ''}`}
                style={{ left: '2px' }}
              >
                {isDarkMode ? '🌙' : '☀️'}
              </div>
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className={`flex items-center gap-2 px-4 py-2 mb-6 border rounded-lg transition-colors duration-200 ${
              isDarkMode ? 'border-[#2d2d30] hover:bg-[#2d2d30] text-gray-200' : 'border-gray-200 hover:bg-gray-50 text-gray-700'
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            <span>New Chat</span>
          </button>

          {/* Common Questions Section */}
          <div>
            <h2 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>Common Questions</h2>
            <div className="space-y-3">
              {commonQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setMessage(question);
                    setIsChatting(true);
                  }}
                  className={`text-left w-full transition-colors duration-200 ${
                    isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed md:hidden inset-0 bg-black bg-opacity-50 z-30"
          onClick={toggleSidebar}
        ></div>
      )}

      {/* Main Content */}
      <div className={`flex-1 flex flex-col ${isChatting ? 'h-screen' : 'min-h-screen'}`}>
        {!isChatting ? (
          <div className="flex-1 flex flex-col items-center justify-center px-4 md:px-8">
            {/* Logo */}
            <div className="max-w-700xl mx-auto mb-6 md:mb-8 pt-8 md:pt-0">
              <img
                src={isDarkMode ? lightLogo : darkLogo}
                alt="RGU Logo"
                className="h-20 md:h-36 w-auto mx-auto"
              />
            </div>

            {/* Cards Grid - Only visible on large screens */}
            <div className="hidden lg:grid max-w-4xl mx-auto grid-cols-4 gap-8 mb-6">
              {cards.map((card, index) => (
                <div
                  key={index}
                  onClick={() =>
                    handleCardClick(Object.values(cardQuestions)[index])
                  }
                  className={`w-[220px] p-8 rounded-xl border h-[260px] ${card.borderColor} cursor-pointer shadow-md transition-all duration-300 flex flex-col items-center text-center ${
                    isDarkMode ? `${card.bgColor.replace('bg-', 'bg-').replace('50', '900/30')} hover:bg-[#3d3d41]` : `${card.bgColor} hover:bg-white hover:shadow-lg`
                  }`}
                >
                  <div className="text-5xl mb-4">{card.icon}</div>
                  <div className={`space-y-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    <div className="text-base font-light">{card.title}</div>
                    <div className="text-base font-medium">{card.subtitle}</div>
                    <div className="text-base font-light">{card.description}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Mobile/Tablet Quick Links */}
            <div className="lg:hidden max-w-md mx-auto space-y-4 mb-6">
              <h2 className={`text-xl font-medium text-center mb-6 ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                Quick Links
              </h2>
              {cards.map((card, index) => (
                <button
                  key={index}
                  onClick={() =>
                    handleCardClick(Object.values(cardQuestions)[index])
                  }
                  className={`w-full p-5 rounded-lg ${card.borderColor} cursor-pointer shadow-md transition-all duration-300 flex items-center gap-3 text-left ${
                    isDarkMode ? `${card.bgColor.replace('bg-', 'bg-').replace('50', '900/30')} hover:bg-[#3d3d41] text-gray-200` : `${card.bgColor} hover:bg-white hover:shadow-lg text-gray-700`
                  }`}
                >
                  <span className="text-3xl">{card.icon}</span>
                  <span className="text-base">{Object.values(cardQuestions)[index]}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {/* Chat Interface */}
        <div
          className={`${
            isChatting ? "flex-1 flex flex-col min-h-0" : ""
          } max-w-9xl mx-auto w-full px-2 md:px-4`}
        >
          {/* Chat History */}
          <div
            className={`overflow-y-auto scroll-smooth pt-4 md:pt-10 pb-24 px-1 sm:px-2 md:px-24 lg:px-32 ${
              isChatting ? "flex-1" : "hidden"
            }`}
          >
            {chatHistory.map((chat, index) => (
              <div
                key={index}
                className={`flex ${
                  chat.type === "user" ? "justify-end" : "justify-start"
                } mb-1.5 sm:mb-2 md:mb-3 lg:mb-4`}
              >
                {chat.type === "bot" && (
                  <div className={`w-7 h-7 md:w-10 md:h-10 p-1 rounded-full flex items-center justify-center mr-1.5 sm:mr-2 md:mr-3 flex-shrink-0 border ${
                    isDarkMode ? 'bg-[#2d2d30] border-[#4d4d4f]' : 'bg-white border-gray-200'
                  }`}>
                    <img
                      src={botIcon}
                      alt="Bot Icon"
                      className="w-5 h-5 md:w-8 md:h-8 object-contain"
                    />
                  </div>
                )}
                <div
                  className={`max-w-[85%] md:max-w-[80%] rounded-lg px-2 sm:px-13 md:px-6 lg:px-8 py-1.5 sm:py-2 md:py-4 lg:py-5 shadow-md hover:shadow-lg transition-shadow ${
                    chat.type === "user"
                      ? isDarkMode ? "bg-[#2d2d30] text-gray-200" : "bg-gray-100 text-black"
                      : isDarkMode ? "bg-[#2d2d30] text-gray-200" : "bg-[#fff] text-black"
                  }`}
                >
                  {chat.text === "loading" ? (
                    /* Loading dots animation */
                    <div className="flex items-center space-x-1.5 py-1 px-2">
                      <div className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: "0ms" }}></div>
                      <div className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: "150ms" }}></div>
                      <div className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: "300ms" }}></div>
                    </div>
                  ) : (
                    <div
                      className="text-[13px] md:text-base
                        [&>h1]:text-[18px] [&>h1]:sm:text-[22px] [&>h1]:md:text-[26px] [&>h1]:lg:text-[28px]
                        [&>h1]:font-bold
                        [&>h1]:mb-3 [&>h1]:sm:mb-4 [&>h1]:md:mb-5 [&>h1]:lg:mb-6
                        [&>h1]:pb-2 [&>h1]:sm:pb-2 [&>h1]:md:pb-3
                        [&>h1]:border-b [&>h1]:border-gray-200
                        [&>h1]:leading-tight [&>h1]:w-full
                        [&>h1+p]:mt-2 [&>h1+p]:sm:mt-3 [&>h1+p]:md:mt-4 [&>h1+p]:lg:mt-5"
                      style={{ color: isDarkMode ? '#e5e7eb' : '#000000' }}
                      dangerouslySetInnerHTML={{ __html: stripInlineStyles(chat.text) }}
                    />
                  )}
                </div>
              </div>
            ))}
            {/* Scroll anchor - auto-scrolls to this element */}
            <div ref={chatEndRef} />
          </div>
        </div>

      {/* Chat Input (static) */}
      <div className={`w-full py-4 md:py-6 ${isDarkMode ? 'bg-[#202123]' : 'bg-white'}`}>
        <form
          onSubmit={handleSubmit}
          className="relative w-[90%] md:w-[600px] mx-auto"
        >
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask me anything..."
            className={`w-full py-3 md:py-4 px-4 md:px-6 pr-10 md:pr-16 rounded-full focus:outline-none text-[14px] md:text-base shadow-sm ${
              isDarkMode
                ? 'bg-[#2d2d30] text-gray-200 placeholder-gray-400'
                : 'bg-gray-100 text-gray-800 placeholder-gray-500'
            }`}
          />
          <div className="absolute right-2 md:right-4 top-1/2 -translate-y-1/2 flex space-x-2">
            <button
              type="submit"
              className={`p-1 md:px-6 text-xl md:text-3xl h-7 md:h-12 w-auto ${
                isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              ➤
            </button>
          </div>
        </form>
      </div>
      </div>
    </div>
  );
}

export default App;
