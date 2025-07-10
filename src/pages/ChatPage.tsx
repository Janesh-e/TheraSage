
import MainChat from "@/components/MainChat";

const ChatPage = () => {
  // Mock user responses for now - in a real app this would come from authentication context
  const userResponses = {
    1: 'User', // userName
    2: 'TheraSage' // botName
  };

  return <MainChat userResponses={userResponses} />;
};

export default ChatPage;
