import React from 'react';
import { FaGraduationCap, FaAward, FaBuilding, FaCreditCard } from 'react-icons/fa';

const cardData = [
  {
    icon: <FaGraduationCap className="text-[#8BB9FE]" />,
    text: "Explore the Eligibility Criteria for B.Tech Programs",
    borderColor: "border-[#8BB9FE]",
  },
  {
    icon: <FaAward className="text-[#98E9AB]" />,
    text: "Explore Scholarship Options and Financial Aid",
    borderColor: "border-[#98E9AB]"
  },
  {
    icon: <FaBuilding className="text-[#E5A0FF]" />,
    text: "Explore Campus Recruitment Opportunities",
    borderColor: "border-[#E5A0FF]"
  },
  {
    icon: <FaCreditCard className="text-[#FFE7A0]" />,
    text: "Learn About Tuition Fees and Payment Methods",
    borderColor: "border-[#FFE7A0]"
  }
];

const Cards = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 px-4 -mt-16">
      {cardData.map((card, index) => (
        <div 
          key={index} 
          className={`bg-white ${card.borderColor} border-2 rounded-2xl p-6 flex flex-col items-center gap-3 cursor-pointer transition-all duration-300 hover:-translate-y-2 min-h-[180px]`}
        >
          <div className="w-12 h-12 rounded-full flex items-center justify-center text-2xl">
            {card.icon}
          </div>
          <p className="text-gray-600 text-sm font-medium text-center">
            {card.text}
          </p>
        </div>
      ))}
    </div>
  );
};

export default Cards; 