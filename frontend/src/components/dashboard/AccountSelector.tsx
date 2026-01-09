import React from 'react';

interface Account {
  account_name: string;
  account_number: string;
  hash_value: string;
}

interface AccountSelectorProps {
  accounts: Account[];
  selectedHash: string;
  onSelect: (hash: string) => void;
  disabled?: boolean; // 新增此屬性
}

const AccountSelector: React.FC<AccountSelectorProps> = ({ accounts, selectedHash, onSelect, disabled }) => {
  return (
    <div className="flex items-center space-x-2">
      <label htmlFor="account-select" className="text-sm font-medium text-slate-400">
        切換帳戶:
      </label>
      <select
        id="account-select"
        value={selectedHash}
        onChange={(e) => onSelect(e.target.value)}
        disabled={disabled}
        className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 disabled:opacity-50"
      >
        {accounts.map((acc) => (
          <option key={acc.hash_value} value={acc.hash_value}>
            {acc.account_name} ({acc.account_number})
          </option>
        ))}
      </select>
    </div>
  );
};

export default AccountSelector;
