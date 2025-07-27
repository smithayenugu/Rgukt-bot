import React, { useState } from "react";
import darkLogo from "../src/assets/darklogo.png"; // Only need dark logo now
import {
  FaGraduationCap,
  FaAward,
  FaBuilding,
  FaCreditCard,
} from "react-icons/fa";

function App() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatting, setIsChatting] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessionId] = useState(Date.now().toString()); // Unique session ID

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setIsChatting(true); // Set chatting mode to true when first message is sent

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, text: message, chat_history: chatHistory }),
      });

      const data = await response.json();

      setChatHistory([
        ...chatHistory,
        { type: "user", text: message },
        { type: "bot", text: data.response },
      ]);

      setMessage("");
    } catch (error) {
      console.error("Error:", error);
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
    setIsChatting(true);
    setMessage("");

    try {
      // Add user question to chat
      setChatHistory((prev) => [
        ...prev,
        {
          type: "user",
          text: question,
        },
      ]);

      // Make API call to get response
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, text: question }),
      });

      const data = await response.json();

      // Add bot response to chat
      setChatHistory((prev) => [
        ...prev,
        {
          type: "bot",
          text: data.response,
        },
      ]);
    } catch (error) {
      console.error("Error:", error);
      setChatHistory((prev) => [
        ...prev,
        {
          type: "bot",
          text: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex min-h-screen bg-white text-black relative">
      {/* Toggle Button */}
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 transition-all duration-300"
        aria-label="Toggle Sidebar"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 text-gray-600"
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
        } transition-all duration-300 border-r bg-white border-gray-200 overflow-hidden h-full z-40 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Sidebar content */}
        <div className="p-6 pt-16 flex flex-col h-full">
          {/* Logo */}
          <div className="mb-6 flex justify-center items-center">
            <img src={darkLogo} alt="RGU Logo" className="h-20 w-auto" />
          </div>

          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 px-4 py-2 mb-6 border rounded-lg border-gray-200 hover:bg-gray-50 transition-colors duration-200"
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
            <h2 className="text-lg font-medium mb-4">Common Questions</h2>
            <div className="space-y-3">
              {commonQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setMessage(question);
                    setIsChatting(true);
                  }}
                  className="text-left w-full text-gray-700 hover:text-gray-900"
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
      <div className="flex-1">
        {!isChatting ? (
          <div className="p-4 md:p-8">
            {/* Logo - with increased top padding on mobile */}
            <div className="max-w-700xl mx-auto mb-8 md:mb-12 pt-8 md:pt-0">
              <img
                src={darkLogo}
                alt="RGU Logo"
                className="h-20 md:h-32 w-auto mx-auto"
              />
            </div>

            {/* Cards Grid - Only visible on large screens */}
            <div className="hidden lg:grid max-w-3xl mx-auto grid-cols-4 gap-6 mb-12">
              {cards.map((card, index) => (
                <div
                  key={index}
                  onClick={() =>
                    handleCardClick(Object.values(cardQuestions)[index])
                  }
                  className={`w-[180px] p-6 rounded-xl border h-[220px] ${card.borderColor} ${card.bgColor} hover:bg-white cursor-pointer hover:shadow-lg shadow-md transition-all duration-300 flex flex-col items-center text-center aspect-square`}
                >
                  <div className="text-4xl mb-4">{card.icon}</div>
                  <div className="space-y-1 text-gray-700">
                    <div className="text-sm font-light">{card.title}</div>
                    <div className="text-sm font-medium">{card.subtitle}</div>
                    <div className="text-sm font-light">{card.description}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Mobile/Tablet Quick Links */}
            <div className="lg:hidden max-w-md mx-auto space-y-4 mb-8">
              <h2 className="text-xl font-medium text-center mb-6">
                Quick Links
              </h2>
              {cards.map((card, index) => (
                <button
                  key={index}
                  onClick={() =>
                    handleCardClick(Object.values(cardQuestions)[index])
                  }
                  className={`w-full p-4 rounded-lg ${card.borderColor} ${card.bgColor} hover:bg-white hover:shadow-lg text-left text-gray-700 transition-all duration-300 shadow-md flex items-center gap-3`}
                >
                  <span className="text-2xl">{card.icon}</span>
                  <span>{Object.values(cardQuestions)[index]}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {/* Chat Interface */}
        <div
          className={`${
            isChatting ? "h-[98vh]" : ""
          } flex flex-col max-w-9xl mx-auto px-2 md:px-4`}
        >
          {/* Chat History */}
          <div
            className={`flex-1 overflow-y-auto pt-4 md:pt-10 px-1 sm:px-2 md:px-24 lg:px-32 ${
              isChatting ? "h-[450px]" : "h-[300px]"
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
                  <div className="w-7 h-7 md:w-10 md:h-10 p-1 rounded-full bg-white flex items-center justify-center mr-1.5 sm:mr-2 md:mr-3 flex-shrink-0 border border-gray-200">
                    <img
                      src="/src/assets/icon.png"
                      alt="Bot Icon"
                      className="w-5 h-5 md:w-8 md:h-8 object-contain"
                    />
                  </div>
                )}
                <div
                  className={`max-w-[85%] md:max-w-[80%] rounded-lg px-2 sm:px-13 md:px-6 lg:px-8 py-1.5 sm:py-2 md:py-4 lg:py-5 shadow-md hover:shadow-lg transition-shadow ${
                    chat.type === "user"
                      ? "bg-gray-100 text-black"
                      : "bg-[#fff] text-black"
                  }`}
                >
                  <div
                    className="text-[13px] md:text-base 
                    [&>h1]:text-[18px] [&>h1]:sm:text-[22px] [&>h1]:md:text-[26px] [&>h1]:lg:text-[28px]
                    [&>h1]:font-bold
                    [&>h1]:mb-3 [&>h1]:sm:mb-4 [&>h1]:md:mb-5 [&>h1]:lg:mb-6
                    [&>h1]:pb-2 [&>h1]:sm:pb-2 [&>h1]:md:pb-3
                    [&>h1]:border-b [&>h1]:border-gray-200
                    [&>h1]:leading-tight
                    [&>h1]:w-full
                    [&>h1]:text-black
                    [&>h1+p]:mt-2 [&>h1+p]:sm:mt-3 [&>h1+p]:md:mt-4 [&>h1+p]:lg:mt-5"
                    dangerouslySetInnerHTML={{ __html: chat.text }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input */}
          <form
            onSubmit={handleSubmit}
            className="relative w-[90%] md:w-[600px] mx-auto mt-2 mb-3 md:mb-4"
          >
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask me anything..."
              className="w-full py-2.5 md:py-4 px-4 md:px-6 pr-10 md:pr-16 rounded-full bg-gray-100 text-gray-800 placeholder-gray-500 focus:outline-none text-[13px] md:text-base"
            />
            <div className="absolute right-2 md:right-4 top-1/2 -translate-y-1/2 flex space-x-2">
              <button
                type="submit"
                className="p-1 md:px-6 text-xl md:text-3xl h-7 md:h-12 w-auto text-gray-500"
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
