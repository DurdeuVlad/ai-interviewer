import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#5b5bd6" },
    background: { default: "#f7f7fb" },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    fontSize: 16,
    h6: { fontSize: "1.5rem" },
    subtitle1: { fontSize: "1.25rem" },
    body1: { fontSize: "1.1rem" },
    body2: { fontSize: "1.05rem" },
    button: { fontSize: "1.05rem", textTransform: "none" },
    caption: { fontSize: "0.9rem" },
  },
  components: {
    MuiIconButton: {
      defaultProps: { size: "large" },
    },
  },
});

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
);
