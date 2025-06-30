
interface ProgressIndicatorProps {
  current: number;
  total: number;
  message: string;
}

const ProgressIndicator = ({ current, total, message }: ProgressIndicatorProps) => {
  const progress = (current / total) * 100;

  return (
    <div className="text-center">
      <div className="bg-white/80 backdrop-blur-sm rounded-3xl p-6 shadow-lg border border-white/70 max-w-md mx-auto">
        <p className="text-base text-gray-700 mb-4 font-medium">{message}</p>
        <div className="w-full bg-gray-200/50 rounded-full h-3 mb-3">
          <div
            className="bg-gradient-to-r from-purple-400 to-pink-400 h-3 rounded-full transition-all duration-700 ease-out shadow-sm"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>{current} of {total} questions</span>
          <span className="text-purple-500 font-medium">{Math.round(progress)}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;
