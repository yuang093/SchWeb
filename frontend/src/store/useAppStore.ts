import { create } from 'zustand';

interface AppState {
  isLiveMode: boolean;
  setLiveMode: (isLive: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  isLiveMode: true, // UX 優化：預設改為 True (Live Mode)
  setLiveMode: (isLive: boolean) => set({ isLiveMode: isLive }),
}));
