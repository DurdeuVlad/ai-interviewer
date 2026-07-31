import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import { startInterview } from "../api/client.js";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { warnBeforeUnload } from "../utils/beforeUnload.js";

export default function TopicEntryView() {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  // See ChatPanel's submittingRef for why a ref is needed here too, not just `loading` state -
  // a rapid double-click could otherwise fire two POST /interviews before the disabled button
  // attribute updates, creating a duplicate, orphaned interview.
  const submittingRef = useRef(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!topic.trim() || submittingRef.current) return;
    submittingRef.current = true;
    setLoading(true);
    setError(null);
    // See ChatPanel's identical guard - a reload while this POST is in flight silently
    // drops the whole "start interview" request with no error shown.
    window.addEventListener("beforeunload", warnBeforeUnload);
    try {
      const submittedTopic = topic.trim();
      const res = await startInterview(submittedTopic);
      navigate(`/interview/${res.interview_id}`, {
        state: { question: res.question, topic: submittedTopic },
      });
    } catch (err) {
      setError(err);
      setLoading(false);
      submittingRef.current = false;
    } finally {
      window.removeEventListener("beforeunload", warnBeforeUnload);
    }
  }

  return (
    <Stack spacing={3} component="form" onSubmit={handleSubmit}>
      <Typography color="text.secondary">
        Pick a topic and have a short conversation with an AI interviewer about it.
      </Typography>
      <TextField
        label="Topic"
        placeholder="e.g. AI in the workplace"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        autoFocus
        fullWidth
      />
      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={!topic.trim() || loading}
        startIcon={loading ? <CircularProgress size={18} color="inherit" /> : null}
      >
        {loading ? "Starting..." : "Start interview"}
      </Button>
      <ErrorBanner error={error} onRetry={() => setError(null)} />
    </Stack>
  );
}
