
interface ProgressIndicatorProps {
  current: number;
  total: number;
  message: string;
}

const ProgressIndicator = ({ current, total, message }: ProgressIndicatorProps) => {
  const progress = (current / total) * 100;

  return (
    <div className="text-center">
      <div className="bg-card/90 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-border max-w-md mx-auto">
        <p className="text-base text-card-foreground mb-4 font-medium">{message}</p>
        <div className="w-full bg-muted/50 rounded-full h-3 mb-3">
          <div
            className="bg-gradient-to-r from-primary to-secondary h-3 rounded-full transition-all duration-700 ease-out shadow-sm"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="flex justify-between items-center text-sm text-muted-foreground">
          <span>{current} of {total} questions</span>
          <span className="text-primary font-medium">{Math.round(progress)}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;
