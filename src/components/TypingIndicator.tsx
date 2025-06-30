
const TypingIndicator = () => {
  return (
    <div className="flex justify-start">
      <div className="bg-white px-4 py-3 rounded-2xl shadow-md border border-gray-100 max-w-xs">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
