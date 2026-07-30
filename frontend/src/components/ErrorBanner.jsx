import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import Button from "@mui/material/Button";
import { Link as RouterLink } from "react-router-dom";

export default function ErrorBanner({ error, onRetry, summaryHref }) {
  if (!error) return null;

  const isAlreadyEnded = error.status === 409;

  return (
    <Alert severity="error" sx={{ my: 2 }}>
      <AlertTitle>Something went wrong</AlertTitle>
      {error.detail || error.message || "An unexpected error occurred."}
      <div style={{ marginTop: 8 }}>
        {isAlreadyEnded && summaryHref ? (
          <Button component={RouterLink} to={summaryHref} size="small" variant="outlined">
            View summary
          </Button>
        ) : (
          onRetry && (
            <Button onClick={onRetry} size="small" variant="outlined">
              Try again
            </Button>
          )
        )}
      </div>
    </Alert>
  );
}
