import React from 'react';
import { MdMic, MdSend } from 'react-icons/md';
import { useTheme } from '../../context/ThemeContext';
import lightlogo from '../../assets/lightlogo.png';
import darklogo from '../../assets/darklogo.png';
import { FaGraduationCap, FaAward, FaBuilding, FaCreditCard } from 'react-icons/fa';

const Home = () => {
  const { isDarkMode } = useTheme();

  const cards = [
    {
      icon: <FaGraduationCap className={`text-4xl opacity-60 ${isDarkMode ? 'text-[#8BB9FE]' : 'text-[#8BB9FE]'}`} />,
      title: "Explore the Eligibility Criteria for B.Tech Programs",
      borderColor: "border-[#8BB9FE]/60"
    },
    {
      icon: <FaAward className={`text-4xl opacity-60 ${isDarkMode ? 'text-[#98E9AB]' : 'text-[#98E9AB]'}`} />,
      title: "Explore Scholarship Options and Financial Aid",
      borderColor: "border-[#98E9AB]/60"
    },
    {
      icon: <FaBuilding className={`text-4xl opacity-60 ${isDarkMode ? 'text-[#E5A0FF]' : 'text-[#E5A0FF]'}`} />,
      title: "Explore Campus Recruitment Opportunities",
      borderColor: "border-[#E5A0FF]/60"
    },
    {
      icon: <FaCreditCard className={`text-4xl opacity-60 ${isDarkMode ? 'text-[#FFE7A0]' : 'text-[#FFE7A0]'}`} />,
      title: "Learn About Tuition Fees and Payment Methods",
      borderColor: "border-[#FFE7A0]/60"
    }
  ];

  return (
    <main className={`min-h-screen flex flex-col font-poppins ${isDarkMode ? 'bg-[#202123]' : 'bg-white'}`}>
      <div className="flex-1 w-full max-w-[850px] mx-auto 
        px-4 md:px-6 lg:px-8 
        flex flex-col">
        
        <div className="flex-1 flex items-center justify-center md:block md:flex-none">
          <div className="text-center md:mb-16">
            <img 
              src={isDarkMode ? lightlogo : darklogo}
              alt="Logo" 
              className="w-auto h-[120px] mx-auto object-contain"
            />
          </div>
        </div>
        
        <div className="hidden md:grid md:grid-cols-2 lg:grid-cols-4 
          gap-6 w-full mx-auto">
          {cards.map((card, index) => (
            <div 
              key={index}
              className={`${card.borderColor} border-[1.4px] rounded-[20px]
                p-6 flex flex-col items-center 
                cursor-pointer transition-all duration-300 
                hover:-translate-y-2
                min-h-[180px]
                justify-between
                ${isDarkMode ? 'bg-[#2d2d30]' : 'bg-white'}`}
            >
              <div className="w-14 h-14 rounded-full flex items-center justify-center">
                {card.icon}
              </div>
              <p className={`text-[15px] leading-[1.4] text-center
                ${isDarkMode ? 'text-gray-200' : 'text-[#4B5563]'}`}>
                {card.title}
              </p>
            </div>
          ))}
        </div>
      </div>
      
      <div className={`fixed bottom-0 left-0 right-0 p-6 
        ${isDarkMode ? 'bg-[#202123]' : 'bg-white'}`}>
        <div className="max-w-[850px] mx-auto">
          <div className={`flex items-center rounded-full px-6 py-4 gap-4 
            ${isDarkMode ? 'bg-[#2d2d30]' : 'bg-[#F3F4F6]'}`}>
            <input
              type="text"
              placeholder="Ask me about admissions, scholarships, placements, and more..."
              className={`flex-1 bg-transparent border-none focus:outline-none text-[15px] font-poppins
                ${isDarkMode 
                  ? 'text-gray-200 placeholder-gray-400' 
                  : 'text-[#6B7280] placeholder-[#9CA3AF]'}`}
            />
            <button className={`p-2 rounded-full transition-colors
              ${isDarkMode 
                ? 'text-gray-400 hover:bg-[#4d4d4f]' 
                : 'text-[#6B7280] hover:bg-gray-200'}`}>
              <MdMic className="text-xl" />
            </button>
            <button className={`p-2 rounded-full transition-colors
              ${isDarkMode 
                ? 'text-gray-400 hover:bg-[#4d4d4f]' 
                : 'text-[#6B7280] hover:bg-gray-200'}`}>
              <MdSend className="text-xl" />
            </button>
          </div>
        </div>
      </div>
    </main>
  );
};

export default Home;
