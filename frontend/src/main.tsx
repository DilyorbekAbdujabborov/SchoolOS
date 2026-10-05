import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { absorbTenantHandoff } from "./lib/api";
import { AuthProvider } from "./lib/auth";
import { ThemeProvider } from "./lib/theme";
import "./index.css";

// A login on the main/apex host hands the session to the tenant subdomain via a
// short-lived base-domain cookie; adopt it into this host's storage before the
// auth layer reads tokens, so the user lands signed in without re-entering.
absorbTenantHandoff();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      // Without a staleTime, every query is stale the instant it resolves, so
      // each component mount refetches — navigating into a section re-fires its
      // requests even though the data was just loaded. 60s of freshness serves
      // cached data on navigation; anything that needs to be live sets its own
      // refetchInterval (lock screen, league board, class access).
      staleTime: 60_000,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
