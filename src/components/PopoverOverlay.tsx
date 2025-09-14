import { motion } from "framer-motion";

export const PopoverOverlay = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="fixed inset-0 z-40 bg-background/30 backdrop-blur-sm"
  />
);
