import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

interface PrivacyContextType {
  isPrivacyMode: boolean;
  togglePrivacyMode: () => void;
  maskValue: (value: number | string, type: 'currency' | 'percent' | 'number') => string;
}

const PrivacyContext = createContext<PrivacyContextType | undefined>(undefined);

export const PrivacyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isPrivacyMode, setIsPrivacyMode] = useState(false);

  const togglePrivacyMode = useCallback(() => {
    setIsPrivacyMode((prev) => !prev);
  }, []);

  const maskValue = useCallback(
    (value: number | string, type: 'currency' | 'percent' | 'number'): string => {
      // 若 type 為 percent，永遠顯示原始值
      if (type === 'percent') {
        return String(value);
      }

      // 若隱私模式開啟，且為 currency 或 number，則隱藏
      if (isPrivacyMode) {
        if (type === 'currency') return '****';
        if (type === 'number') return '----';
      }

      // 否則回傳原始格式化後的字串（假設傳進來的是已經格式化好的，或者直接轉字串）
      return String(value);
    },
    [isPrivacyMode]
  );

  return (
    <PrivacyContext.Provider value={{ isPrivacyMode, togglePrivacyMode, maskValue }}>
      {children}
    </PrivacyContext.Provider>
  );
};

export const usePrivacy = () => {
  const context = useContext(PrivacyContext);
  if (context === undefined) {
    throw new Error('usePrivacy must be used within a PrivacyProvider');
  }
  return context;
};
