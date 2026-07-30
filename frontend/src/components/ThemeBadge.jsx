import Chip from "@mui/material/Chip";

const COLOR_BY_SENTIMENT = {
  positive: "success",
  negative: "error",
  mixed: "warning",
  neutral: "default",
};

export default function ThemeBadge({ sentiment }) {
  return (
    <Chip
      label={sentiment}
      color={COLOR_BY_SENTIMENT[sentiment] || "default"}
      size="small"
      variant="outlined"
    />
  );
}
