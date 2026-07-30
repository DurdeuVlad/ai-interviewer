import Stack from "@mui/material/Stack";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";

export default function ThinkingIndicator() {
  return (
    <Stack direction="row" spacing={1.5} sx={{ py: 1, alignItems: "center" }}>
      <CircularProgress size={18} thickness={5} />
      <Typography variant="body2" color="text.secondary">
        Thinking...
      </Typography>
    </Stack>
  );
}
