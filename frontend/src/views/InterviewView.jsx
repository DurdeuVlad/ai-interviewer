import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import { Link as RouterLink } from "react-router-dom";
import { getInterview, submitAnswer } from "../api/client.js";
import ErrorBanner from "../components/ErrorBanner.jsx";
import ThinkingIndicator from "../components/ThinkingIndicator.jsx";
import TypewriterText from "../components/TypewriterText.jsx";

export default function InterviewView() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [transcript, setTranscript] = useState([]);
  const [question, setQuestion] = useState(location.state?.question || null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(!location.state?.question);
  const [error, setError] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const lastAnswerRef = useRef("");

  useEffect(() => {
    if (location.state?.question) return; // already have what we need, no page reload/direct nav

    let cancelled = false;
    (async () => {
      try {
        const detail = await getInterview(id);
        if (cancelled) return;
        if (detail.status === "completed") {
          navigate(`/interview/${id}/summary`, { replace: true });
          return;
        }
        setTranscript(detail.transcript.slice(0, -1));
        setQuestion(detail.transcript[detail.transcript.length - 1]?.content || null);
      } catch (err) {
        if (!cancelled) setLoadError(err);
      } finally {
        if (!cancelled) setInitializing(false);
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!answer.trim() || loading) return;
    const submittedAnswer = answer.trim();
    lastAnswerRef.current = submittedAnswer;
    setLoading(true);
    setError(null);
    try {
      const res = await submitAnswer(id, submittedAnswer);
      setTranscript((prev) => [
        ...prev,
        { role: "assistant", content: question },
        { role: "user", content: submittedAnswer },
      ]);
      setAnswer("");
      if (res.done) {
        navigate(`/interview/${id}/summary`);
      } else {
        setQuestion(res.question);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  function handleRetry() {
    setAnswer(lastAnswerRef.current);
    setError(null);
  }

  if (initializing) {
    return <ThinkingIndicator />;
  }

  if (loadError) {
    return (
      <Stack spacing={2}>
        <ErrorBanner error={loadError} />
        <Button component={RouterLink} to="/" variant="outlined" sx={{ alignSelf: "flex-start" }}>
          Start a new interview
        </Button>
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      {transcript.length > 0 && (
        <Stack spacing={1.5} sx={{ maxHeight: 320, overflowY: "auto" }}>
          {transcript.map((message, index) => (
            <Paper
              key={index}
              variant="outlined"
              sx={{
                p: 1.5,
                bgcolor: message.role === "assistant" ? "grey.50" : "primary.50",
                textAlign: "left",
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {message.role === "assistant" ? "Interviewer" : "You"}
              </Typography>
              <Typography variant="body2">{message.content}</Typography>
            </Paper>
          ))}
        </Stack>
      )}

      <Box sx={{ textAlign: "left" }}>
        {question && <TypewriterText text={question} variant="h6" />}
      </Box>

      <Stack spacing={2} component="form" onSubmit={handleSubmit}>
        <TextField
          label="Your answer"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          multiline
          minRows={2}
          autoFocus
          fullWidth
          disabled={loading}
        />
        <Button type="submit" variant="contained" disabled={!answer.trim() || loading}>
          Send
        </Button>
      </Stack>

      {loading && <ThinkingIndicator />}
      <ErrorBanner error={error} onRetry={handleRetry} summaryHref={`/interview/${id}/summary`} />
    </Stack>
  );
}
