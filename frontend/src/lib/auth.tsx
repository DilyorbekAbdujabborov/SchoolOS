import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

import { api, login as apiLogin, logout as apiLogout, onSchoolTimeLock, tokenStorage } from "./api";
import type { CurrentUser } from "../types";

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  schoolLockMessage: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [schoolLockMessage, setSchoolLockMessage] = useState<string | null>(null);
  const [hasToken, setHasToken] = useState(() => Boolean(tokenStorage.getAccess()));

  // The lock is global: `/auth/me/` is exempt (so the app can always resolve
  // the signed-in user), which means the 423 arrives on the *data* endpoints
  // instead. Listen for it app-wide rather than tying it to any one query.
  useEffect(() => onSchoolTimeLock(setSchoolLockMessage), []);

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    enabled: hasToken,
    retry: false,
    queryFn: async () => (await api.get<CurrentUser>("/auth/me/")).data,
  });

  async function login(email: string, password: string) {
    await apiLogin(email, password);
    setHasToken(true);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  function logout() {
    apiLogout();
    setHasToken(false);
    queryClient.setQueryData(["me"], null);
    queryClient.clear();
  }

  return (
    <AuthContext.Provider
      value={{
        user: user ?? null,
        isLoading: hasToken && isLoading,
        isAuthenticated: Boolean(user),
        schoolLockMessage,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
