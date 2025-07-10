/**
 * Removes emojis and special characters from text for better speech synthesis
 */
export const cleanTextForSpeech = (text: string): string => {
  // Remove emojis using regex
  const emojiRegex = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu;
  
  // Remove other unicode symbols and special characters but keep basic punctuation
  const cleanedText = text
    .replace(emojiRegex, '') // Remove emojis
    .replace(/[^\w\s.,!?;:'"()-]/g, '') // Keep only alphanumeric, whitespace, and basic punctuation
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .trim(); // Remove leading/trailing whitespace
  
  return cleanedText;
};
