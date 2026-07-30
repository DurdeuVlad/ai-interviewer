import { useEffect, useRef, useState } from "react";
import { useParams, useLocation, useNavigate, Link as RouterLink } from "react-router-dom";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { getInterview, submitAnswer, getSummary, exportJsonUrl, exportPdfUrl } from "../api/client.js";
import ChatHeader from "../components/ChatHeader.jsx";
import ChatBubble from "../components/ChatBubble.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import ThinkingIndicator from "../components/ThinkingIndicator.jsx";
import TypewriterText from "../components/TypewriterText.jsx";
import InterviewSummaryCard from "../components/InterviewSummaryCard.jsx";
import TopicEntryView from "./TopicEntryView.jsx";
import { notifyInterviewsChanged } from "../utils/interviewEvents.js";

export default function ChatPanel({ onMenuClick }) {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [transcript, setTranscript] = useState([]);
  const [question, setQuestion] = useState(location.state?.question || null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(Boolean(id) && !location.state?.question);
  const [error, setError] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [status, setStatus] = useState("in_progress");
  const [topic, setTopic] = useState(location.state?.topic || null);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(null);
  const [summaryRetryKey, setSummaryRetryKey] = useState(0);

  const lastAnswerRef = useRef("");
  const bottomRef = useRef(null);

  // Reset all per-interview state whenever the id changes (covers "/" <-> "/interview/:id" too).
  useEffect(() => {
    setTranscript([]);
    setQuestion(location.state?.question || null);
    setAnswer("");
    setLoading(false);
    setError(null);
    setLoadError(null);
    setStatus("in_progress");
    setTopic(location.state?.topic || null);
    setSummary(null);
    setSummaryLoading(false);
    setSummaryError(null);
    setInitializing(Boolean(id) && !location.state?.question);

    if (location.state?.question) {
      // React Router persists navigate(path, {state}) into the browser's *native* History
      // API entry for that URL - it survives a hard reload of the same URL, long after the
      // interview has moved on. Scrub it once consumed so a future reload of this exact URL
      // falls through to a real getInterview(id) fetch instead of reading this stale snapshot
      // forever (this is what caused a completed interview to show only the first question on
      // reload during testing).
      navigate(location.pathname, { replace: true, state: {} });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Initial load for a specific interview id, unless nav state already supplied the first question.
  useEffect(() => {
    if (!id || location.state?.question) return;

    let cancelled = false;
    (async () => {
      try {
        const detail = await getInterview(id);
        if (cancelled) return;
        setTopic(detail.topic);
        setStatus(detail.status);
        if (detail.status === "completed") {
          setTranscript(detail.transcript);
        } else {
          setTranscript(detail.transcript.slice(0, -1));
          setQuestion(detail.transcript[detail.transcript.length - 1]?.content || null);
        }
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

  // Fetch the summary inline once the interview is completed.
  useEffect(() => {
    if (status !== "completed" || !id) return;
    let cancelled = false;
    (async () => {
      setSummaryLoading(true);
      setSummaryError(null);
      try {
        const res = await getSummary(id);
        if (!cancelled) setSummary(res);
      } catch (err) {
        if (!cancelled) setSummaryError(err);
      } finally {
        if (!cancelled) setSummaryLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, status, summaryRetryKey]);

  // Auto-scroll to the latest content. Keyed on question/status/summary identity, not on every
  // TypewriterText tick (which mutates its own internal string every ~12ms without changing the
  // question prop) - avoids jittery re-scrolling during the typing animation.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript.length, question, status, summary]);

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
        setStatus("completed");
        notifyInterviewsChanged();
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

  if (!id) {
    return (
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <ChatHeader title="New chat" onMenuClick={onMenuClick} />
        <Box sx={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", p: 3 }}>
          <Box sx={{ width: "100%", maxWidth: 480 }}>
            <TopicEntryView />
          </Box>
        </Box>
      </Box>
    );
  }

  if (initializing) {
    return (
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <ChatHeader title="Loading..." onMenuClick={onMenuClick} />
        <Box sx={{ p: 3 }}>
          <ThinkingIndicator />
        </Box>
      </Box>
    );
  }

  if (loadError) {
    return (
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <ChatHeader title="Not found" onMenuClick={onMenuClick} />
        <Stack spacing={2} sx={{ p: 3 }}>
          <ErrorBanner error={loadError} />
          <Button component={RouterLink} to="/" variant="outlined" sx={{ alignSelf: "flex-start" }}>
            Start a new interview
          </Button>
        </Stack>
      </Box>
    );
  }

  return (
    <Box sx={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
      <ChatHeader title={topic || "Interview"} onMenuClick={onMenuClick} />

      <Box sx={{ flex: 1, overflowY: "auto", p: 2 }}>
        <Stack spacing={1.5}>
          {transcript.map((message, index) => (
            <ChatBubble key={index} sender={message.role === "user" ? "user" : "assistant"}>
              <Typography variant="body2">{message.content}</Typography>
            </ChatBubble>
          ))}

          {status !== "completed" && question && (
            <ChatBubble sender="assistant">
              <TypewriterText text={question} variant="body2" />
            </ChatBubble>
          )}

          {status === "completed" && (
            <>
              {summaryLoading && <ThinkingIndicator />}
              {summaryError && (
                <ErrorBanner error={summaryError} onRetry={() => setSummaryRetryKey((k) => k + 1)} />
              )}
              {summary && (
                <InterviewSummaryCard
                  summary={summary}
                  interviewId={id}
                  exportJsonUrl={exportJsonUrl}
                  exportPdfUrl={exportPdfUrl}
                />
              )}
            </>
          )}

          <div ref={bottomRef} />
        </Stack>
      </Box>

      {status !== "completed" && (
        <Box sx={{ borderTop: 1, borderColor: "divider", p: 2 }}>
          {loading && <ThinkingIndicator />}
          <ErrorBanner error={error} onRetry={handleRetry} />
          <Stack direction="row" spacing={1} component="form" onSubmit={handleSubmit}>
            <TextField
              placeholder="Type your answer..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              fullWidth
              size="small"
              autoFocus
              disabled={loading}
            />
            <Button type="submit" variant="contained" disabled={!answer.trim() || loading}>
              Send
            </Button>
          </Stack>
        </Box>
      )}
    </Box>
  );
}
