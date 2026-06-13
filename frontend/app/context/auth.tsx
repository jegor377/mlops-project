import { createContext, useCallback, useContext, useEffect, useState } from "react";

type AuthUser = { email: string; id: number; is_active: boolean } | null;
type AuthCtx = {
  user: AuthUser;
  loading: boolean;
  setUser: (u: AuthUser) => void;
  refetch: () => Promise<void>;
};

const AuthContext = createContext<AuthCtx>({
  user: null,
  loading: true,
  setUser: () => {},
  refetch: async () => {},
});

async function fetchMe(): Promise<AuthUser> {
  try {
    const r = await fetch("/auth/me", { credentials: "include" });
    return r.ok ? r.json() : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser>(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    const data = await fetchMe();
    setUser(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMe().then(data => {
      setUser(data);
      setLoading(false);
    });
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, setUser, refetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);