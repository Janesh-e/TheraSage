
interface ProgressIndicatorProps {
  current: number;
  total: number;
  message: string;
}

const ProgressIndicator = ({ current, total, message }: ProgressIndicatorProps) => {
  const progress = (current / total) * 100;

  return (
    <div className="mb-8 text-center">
      <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-4 shadow-lg border border-white/50 max-w-sm mx-auto">
        <p className="text-sm text-gray-600 mb-3">{message}</p>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-purple-400 to-pink-400 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {current} of {total} questions
        </p>
      </div>
    </div>
  );
};

export default ProgressIndicator;
