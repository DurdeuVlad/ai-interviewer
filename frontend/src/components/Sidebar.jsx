import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import AddCommentIcon from "@mui/icons-material/AddComment";
import { listInterviews } from "../api/client.js";
import { onInterviewsChanged } from "../utils/interviewEvents.js";

function formatDate(isoString) {
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();

  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchList() {
      setLoading(true);
      try {
        const res = await listInterviews();
        if (!cancelled) {
          setInterviews(res.interviews);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchList();
    const unsubscribe = onInterviewsChanged(fetchList);

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [location.pathname]);

  return (
    <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column" }}>
      <Stack
        direction="row"
        sx={{ p: 2, alignItems: "center", justifyContent: "space-between" }}
      >
        <Typography variant="h6" fontWeight={600}>
          AI Interviewer
        </Typography>
        <IconButton color="primary" onClick={() => navigate("/")} aria-label="New chat">
          <AddCommentIcon />
        </IconButton>
      </Stack>
      <Divider />

      <Box sx={{ flex: 1, overflowY: "auto" }}>
        {loading && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
            Loading conversations...
          </Typography>
        )}
        {error && (
          <Typography variant="body2" color="error" sx={{ p: 2 }}>
            Couldn't load conversations.
          </Typography>
        )}
        {!loading && !error && interviews.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
            No conversations yet — start one!
          </Typography>
        )}
        <List disablePadding>
          {interviews.map((item) => (
            <ListItemButton
              key={item.interview_id}
              selected={String(item.interview_id) === id}
              onClick={() => navigate(`/interview/${item.interview_id}`)}
            >
              <ListItemText
                primary={item.topic}
                secondary={formatDate(item.created_at)}
                slotProps={{ primary: { noWrap: true } }}
              />
              <Chip
                label={item.status === "completed" ? "Done" : "Active"}
                size="small"
                color={item.status === "completed" ? "default" : "primary"}
                variant="outlined"
              />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </Box>
  );
}
