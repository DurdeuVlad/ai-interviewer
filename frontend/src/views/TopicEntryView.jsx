import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import { startInterview } from "../api/client.js";
import ErrorBanner from "../components/ErrorBanner.jsx";

export default function TopicEntryView() {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    if (!topic.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const submittedTopic = topic.trim();
      const res = await startInterview(submittedTopic);
      navigate(`/interview/${res.interview_id}`, {
        state: { question: res.question, topic: submittedTopic },
      });
    } catch (err) {
      setError(err);
      setLoading(false);
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
