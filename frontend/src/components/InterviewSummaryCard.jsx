import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import { Link as RouterLink } from "react-router-dom";
import ThemeBadge from "./ThemeBadge.jsx";
import { sentimentLabel } from "../utils/sentiment.js";

export default function InterviewSummaryCard({ summary, interviewId, exportJsonUrl, exportPdfUrl }) {
  const {
    themes,
    key_points: keyPoints,
    feedback,
    keyword_extract: keywords,
    sentiment_score: sentimentScore,
  } = summary;

  return (
    <Paper
      variant="outlined"
      sx={{ p: 3, bgcolor: "background.paper", textAlign: "left" }}
    >
      <Typography variant="overline" color="text.secondary">
        Interview summary
      </Typography>

      <Stack spacing={3} sx={{ mt: 1 }}>
        <Stack spacing={1.5}>
          <Typography variant="h6">Themes</Typography>
          {themes.length === 0 ? (
            <Typography color="text.secondary">No clear themes emerged from this conversation.</Typography>
          ) : (
            <Stack spacing={1.5}>
              {themes.map((theme, index) => (
                <Paper key={index} variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={1} sx={{ mb: 0.5, alignItems: "center" }}>
                    <Typography fontWeight={600}>{theme.name}</Typography>
                    <ThemeBadge sentiment={theme.sentiment} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    &ldquo;{theme.quote}&rdquo;
                  </Typography>
                </Paper>
              ))}
            </Stack>
          )}
        </Stack>

        <Divider />

        <Stack spacing={1}>
          <Typography variant="h6">Key points</Typography>
          {keyPoints.length === 0 ? (
            <Typography color="text.secondary">
              No concrete points could be drawn from the responses given.
            </Typography>
          ) : (
            <Stack component="ul" sx={{ pl: 3, m: 0 }} spacing={0.5}>
              {keyPoints.map((point, index) => (
                <Typography component="li" variant="body2" key={index}>
                  {point}
                </Typography>
              ))}
            </Stack>
          )}
        </Stack>

        {(feedback.positives.length > 0 || feedback.constructive.length > 0) && (
          <>
            <Divider />
            <Stack spacing={0.5}>
              <Typography variant="h6">Feedback on the interview</Typography>
              {feedback.positives.map((point, index) => (
                <Typography variant="body2" color="success.main" key={`pos-${index}`}>
                  + {point}
                </Typography>
              ))}
              {feedback.constructive.map((point, index) => (
                <Typography variant="body2" color="warning.main" key={`con-${index}`}>
                  - {point}
                </Typography>
              ))}
            </Stack>
          </>
        )}

        <Divider />

        <Stack spacing={1}>
          <Typography variant="h6">Bonus analysis</Typography>
          {keywords.length > 0 && (
            <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
              {keywords.map((word) => (
                <Chip key={word} label={word} size="small" />
              ))}
            </Stack>
          )}
          {sentimentScore !== null && (
            <Typography variant="body2">
              Overall sentiment: {sentimentScore.toFixed(3)} ({sentimentLabel(sentimentScore)})
            </Typography>
          )}
        </Stack>

        <Divider />

        <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
          <Button variant="outlined" component="a" href={exportJsonUrl(interviewId)} download>
            Download JSON
          </Button>
          <Button variant="outlined" component="a" href={exportPdfUrl(interviewId)} download>
            Download PDF
          </Button>
          <Button component={RouterLink} to="/" variant="text">
            Start a new interview
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
